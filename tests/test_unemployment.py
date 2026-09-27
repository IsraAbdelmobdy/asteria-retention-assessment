import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from asteria_retention.adapters.eurostat import (
    EurostatDownload,
    build_unemployment_url,
    parse_unemployment_response,
)
from asteria_retention.domain.external import (
    aggregate_monthly_unemployment_to_quarters,
)
from asteria_retention.pipeline.unemployment import ingest_unemployment


def response_bytes(values=None):
    payload = {
        "version": "2.0",
        "class": "dataset",
        "updated": "2026-09-22T09:00:00Z",
        "id": ["freq", "unit", "geo", "time"],
        "size": [1, 1, 2, 3],
        "dimension": {
            "freq": {"category": {"index": {"M": 0}}},
            "unit": {"category": {"index": {"PC_ACT": 0}}},
            "geo": {"category": {"index": {"BG": 0, "EL": 1}}},
            "time": {
                "category": {
                    "index": {"2021-01": 0, "2021-02": 1, "2021-03": 2}
                }
            },
        },
        "value": values if values is not None else [5.0, 5.2, 5.4, 10.0, 10.2, 10.4],
        "status": {"4": "p"},
    }
    return json.dumps(payload).encode("utf-8")


def parse(content):
    return parse_unemployment_response(
        content,
        country_mapping={"BG": "BG", "EL": "GR"},
        request_url="https://example.test/eurostat",
        retrieved_at_utc="2026-09-25T10:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
        dataset_code="une_rt_m",
    )


def test_url_contains_repeated_country_parameters_and_approved_dimensions():
    url = build_unemployment_url(
        {
            "dataset": "une_rt_m",
            "parameters": {
                "freq": "M",
                "unit": "PC_ACT",
                "s_adj": "SA",
                "age": "TOTAL",
                "sex": "T",
            },
        },
        {
            "BG": {"eurostat_code": "BG"},
            "GR": {"eurostat_code": "EL"},
        },
        start_period="2021-01",
        end_period="2025-12",
    )

    assert "dataset" not in url
    assert "une_rt_m?" in url
    assert "geo=BG&geo=EL" in url
    assert "s_adj=SA" in url
    assert "sinceTimePeriod=2021-01" in url


def test_parser_preserves_provider_code_and_maps_greece_to_gr():
    monthly = parse(response_bytes())

    greek = monthly.loc[monthly["country_code"].eq("GR")]
    assert len(monthly) == 6
    assert set(greek["provider_country_code"]) == {"EL"}
    assert list(greek["value"]) == [10.0, 10.2, 10.4]
    assert greek.loc[greek["reference_period"].eq("2021-02"), "observation_status"].iloc[0] == "p"


def test_complete_quarter_is_arithmetic_mean_of_three_months():
    quarterly = aggregate_monthly_unemployment_to_quarters(parse(response_bytes()))
    greek = quarterly.loc[quarterly["country_code"].eq("GR")].iloc[0]

    assert greek["monthly_observations"] == 3
    assert greek["coverage_status"] == "COMPLETE"
    assert greek["unemployment_rate"] == pytest.approx(10.2)


def test_csv_round_trip_blank_status_does_not_break_quarterly_aggregation(tmp_path):
    monthly = parse(response_bytes())
    path = tmp_path / "monthly.csv"
    monthly.to_csv(path, index=False)
    restored = pd.read_csv(path)

    quarterly = aggregate_monthly_unemployment_to_quarters(restored)

    assert len(quarterly) == 2
    assert set(quarterly["coverage_status"]) == {"COMPLETE"}


def test_missing_monthly_value_makes_quarter_incomplete_instead_of_partial_mean():
    monthly = parse(response_bytes(values={"0": 5.0, "1": 5.2, "3": 10.0, "4": 10.2, "5": 10.4}))
    quarterly = aggregate_monthly_unemployment_to_quarters(monthly)
    bulgaria = quarterly.loc[quarterly["country_code"].eq("BG")].iloc[0]

    assert bulgaria["monthly_observations"] == 3
    assert bulgaria["available_monthly_values"] == 2
    assert bulgaria["coverage_status"] == "INCOMPLETE"
    assert pd.isna(bulgaria["unemployment_rate"])


def test_pipeline_preserves_raw_and_writes_monthly_and_quarterly_files(tmp_path):
    content = response_bytes()
    download = EurostatDownload(
        content=content,
        request_url="https://example.test/eurostat",
        retrieved_at_utc="2026-09-25T10:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    result = ingest_unemployment(
        Path("."),
        tmp_path / "raw",
        tmp_path / "canonical",
        tmp_path / "output",
        download=download,
    )

    assert result.summary["returned_monthly_rows"] == 6
    assert result.summary["complete_quarters"] == 2
    assert len(list((tmp_path / "raw").glob("unemployment_*.json"))) == 1
    assert (tmp_path / "canonical" / "unemployment_monthly.csv").is_file()
    assert (tmp_path / "output" / "unemployment_quarterly.csv").is_file()
    assert (tmp_path / "output" / "unemployment_ingestion_summary.json").is_file()
