import hashlib
import json
from pathlib import Path

import pandas as pd

from asteria_retention.adapters.world_bank import (
    WorldBankDownload,
    build_inflation_url,
    parse_inflation_response,
)
from asteria_retention.pipeline.inflation import ingest_inflation


def response_bytes():
    payload = [
        {
            "page": 1,
            "pages": 1,
            "per_page": "100",
            "total": 4,
            "sourceid": "2",
            "lastupdated": "2026-07-13",
        },
        [
            {
                "indicator": {
                    "id": "FP.CPI.TOTL.ZG",
                    "value": "Inflation, consumer prices (annual %)",
                },
                "country": {"id": "BG", "value": "Bulgaria"},
                "countryiso3code": "BGR",
                "date": "2022",
                "value": 13.0,
                "obs_status": "",
            },
            {
                "indicator": {
                    "id": "FP.CPI.TOTL.ZG",
                    "value": "Inflation, consumer prices (annual %)",
                },
                "country": {"id": "BG", "value": "Bulgaria"},
                "countryiso3code": "BGR",
                "date": "2021",
                "value": 3.3,
                "obs_status": "",
            },
            {
                "indicator": {
                    "id": "FP.CPI.TOTL.ZG",
                    "value": "Inflation, consumer prices (annual %)",
                },
                "country": {"id": "GR", "value": "Greece"},
                "countryiso3code": "GRC",
                "date": "2021",
                "value": 1.2,
                "obs_status": "",
            },
        ],
    ]
    return json.dumps(payload).encode("utf-8")


def parse(content):
    return parse_inflation_response(
        content,
        country_mapping={"BGR": "BG", "GRC": "GR"},
        start_year=2021,
        end_year=2022,
        request_url="https://example.test/world-bank",
        retrieved_at_utc="2026-09-25T14:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
    )


def test_url_uses_indicator_country_codes_and_annual_range():
    url = build_inflation_url(
        {
            "BG": {"world_bank_code": "BGR"},
            "GR": {"world_bank_code": "GRC"},
        },
        start_year=2021,
        end_year=2025,
    )

    assert "BGR;GRC" in url
    assert "/indicator/FP.CPI.TOTL.ZG" in url
    assert "format=json" in url
    assert "date=2021%3A2025" in url or "date=2021:2025" in url


def test_parser_maps_country_codes_and_preserves_annual_frequency():
    annual, metadata = parse(response_bytes())
    bulgaria_2022 = annual.loc[
        annual["country_code"].eq("BG")
        & annual["reference_year"].eq(2022)
    ].iloc[0]

    assert len(annual) == 4
    assert bulgaria_2022["provider_country_code"] == "BGR"
    assert bulgaria_2022["value"] == 13.0
    assert bulgaria_2022["native_frequency"] == "annual"
    assert "not expanded" in bulgaria_2022["transformation_note"]
    assert metadata["source_id"] == "2"


def test_missing_country_year_is_retained_as_null_and_not_guessed():
    annual, _ = parse(response_bytes())
    missing = annual.loc[
        annual["country_code"].eq("GR")
        & annual["reference_year"].eq(2022)
    ].iloc[0]

    assert pd.isna(missing["value"])
    assert missing["provider_country_code"] == "GRC"


def test_attribution_and_license_are_preserved():
    annual, _ = parse(response_bytes())

    assert set(annual["license"]) == {"CC BY 4.0"}
    assert annual["attribution"].str.contains("World Development Indicators").all()
    assert annual["source_organization"].str.contains("International Monetary Fund").all()


def test_pipeline_preserves_raw_and_writes_annual_file(tmp_path):
    content = response_bytes()
    download = WorldBankDownload(
        content=content,
        request_url="https://example.test/world-bank",
        retrieved_at_utc="2026-09-25T14:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    result = ingest_inflation(
        Path("."),
        tmp_path / "raw",
        tmp_path / "canonical",
        tmp_path / "output",
        download=download,
    )

    assert result.summary["canonical_annual_rows"] == 30
    assert result.summary["available_annual_values"] == 3
    assert result.summary["missing_annual_values"] == 27
    assert result.summary["frequency_treatment"] == "annual_values_not_expanded"
    assert len(list((tmp_path / "raw").glob("inflation_*.json"))) == 1
    assert (
        tmp_path / "canonical" / "consumer_price_inflation_annual.csv"
    ).is_file()
    assert (tmp_path / "output" / "inflation_ingestion_summary.json").is_file()
