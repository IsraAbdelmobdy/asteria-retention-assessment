import hashlib
import json
from pathlib import Path

from asteria_retention.adapters.eurostat import (
    EurostatDownload,
    build_job_vacancy_url,
    parse_job_vacancy_response,
)
from asteria_retention.pipeline.job_vacancy import ingest_job_vacancy


def response_bytes():
    payload = {
        "version": "2.0",
        "class": "dataset",
        "updated": "2026-03-21T11:00:00Z",
        "id": [
            "freq",
            "s_adj",
            "nace_r2",
            "sizeclas",
            "indic_em",
            "geo",
            "time",
        ],
        "size": [1, 1, 1, 1, 1, 2, 2],
        "dimension": {
            "freq": {"category": {"index": {"Q": 0}}},
            "s_adj": {"category": {"index": {"SA": 0}}},
            "nace_r2": {"category": {"index": {"B-S": 0}}},
            "sizeclas": {"category": {"index": {"TOTAL": 0}}},
            "indic_em": {"category": {"index": {"JVR": 0}}},
            "geo": {"category": {"index": {"EL": 0, "IT": 1}}},
            "time": {"category": {"index": {"2021-Q1": 0, "2021-Q2": 1}}},
        },
        "value": [1.0, 1.1, 2.0, 2.1],
        "status": {"0": "p", "3": "p"},
    }
    return json.dumps(payload).encode("utf-8")


def parse(content):
    return parse_job_vacancy_response(
        content,
        country_mapping={"EL": "GR", "IT": "IT"},
        request_url="https://example.test/eurostat",
        retrieved_at_utc="2026-09-25T12:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
        dataset_code="jvs_q_nace2",
    )


def test_job_vacancy_url_locks_approved_dataset_scope_and_period():
    url = build_job_vacancy_url(
        {
            "dataset": "jvs_q_nace2",
            "parameters": {
                "freq": "Q",
                "s_adj": "SA",
                "nace_r2": "B-S",
                "sizeclas": "TOTAL",
                "indic_em": "JVR",
            },
        },
        {"GR": {"eurostat_code": "EL"}, "IT": {"eurostat_code": "IT"}},
        start_period="2021-Q1",
        end_period="2025-Q4",
    )

    assert "jvs_q_nace2?" in url
    assert "nace_r2=B-S" in url
    assert "s_adj=SA" in url
    assert "geo=EL&geo=IT" in url
    assert "untilTimePeriod=2025-Q4" in url


def test_parser_preserves_provisional_flags_and_native_quarters():
    quarterly = parse(response_bytes())
    first_greece = quarterly.loc[
        quarterly["country_code"].eq("GR")
        & quarterly["reference_period"].eq("2021-Q1")
    ].iloc[0]

    assert len(quarterly) == 4
    assert first_greece["provider_country_code"] == "EL"
    assert first_greece["value"] == 1.0
    assert first_greece["observation_status"] == "p"
    assert first_greece["is_provisional"]
    assert first_greece["quarter_end"] == "2021-03-31"


def test_every_italy_row_has_visible_reduced_coverage_warning():
    quarterly = parse(response_bytes())
    italy = quarterly.loc[quarterly["country_code"].eq("IT")]
    greece = quarterly.loc[quarterly["country_code"].eq("GR")]

    assert set(italy["coverage_note_code"]) == {
        "ITALY_REDUCED_PUBLIC_SECTOR_COVERAGE"
    }
    assert set(greece["coverage_note_code"]) == {""}


def test_pipeline_preserves_raw_and_writes_quarterly_file(tmp_path):
    content = response_bytes()
    download = EurostatDownload(
        content=content,
        request_url="https://example.test/eurostat",
        retrieved_at_utc="2026-09-25T12:00:00Z",
        sha256=hashlib.sha256(content).hexdigest(),
    )

    result = ingest_job_vacancy(
        Path("."),
        tmp_path / "raw",
        tmp_path / "canonical",
        tmp_path / "output",
        download=download,
    )

    assert result.summary["returned_quarterly_rows"] == 4
    assert result.summary["provisional_values"] == 2
    assert result.summary["italy_coverage_warning_rows"] == 2
    assert result.summary["classification_version"] == "NACE Rev. 2"
    assert len(list((tmp_path / "raw").glob("job_vacancy_*.json"))) == 1
    assert (tmp_path / "canonical" / "job_vacancy_quarterly.csv").is_file()
    assert (tmp_path / "output" / "job_vacancy_ingestion_summary.json").is_file()
