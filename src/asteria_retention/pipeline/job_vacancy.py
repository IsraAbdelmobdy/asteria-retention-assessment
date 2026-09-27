"""Download and preserve the approved Eurostat quarterly job-vacancy series."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asteria_retention.adapters.eurostat import (
    EurostatDownload,
    EurostatSourceError,
    build_job_vacancy_url,
    download_eurostat_json,
    parse_job_vacancy_response,
)
from asteria_retention.config import load_project_config
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv


@dataclass(frozen=True)
class JobVacancyIngestionResult:
    quarterly: pd.DataFrame
    summary: dict[str, object]


def ingest_job_vacancy(
    project_root: Path,
    raw_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    *,
    download: EurostatDownload | None = None,
) -> JobVacancyIngestionResult:
    config = load_project_config(project_root)["indicators"]
    analysis = config["analysis"]
    countries = config["countries"]
    indicator = config["indicators"]["job_vacancy_rate"]
    if str(indicator["dataset"]) != "jvs_q_nace2":
        raise EurostatSourceError(
            "approved historical contract requires jvs_q_nace2; a dataset-version "
            "migration must be explicitly reviewed"
        )

    start_period = str(
        indicator.get(
            "ingestion_start", f"{str(analysis['start_date'])[:4]}-Q1"
        )
    )
    end_period = f"{str(analysis['end_date'])[:4]}-Q4"
    url = build_job_vacancy_url(
        indicator,
        countries,
        start_period=start_period,
        end_period=end_period,
    )
    downloaded = download or download_eurostat_json(url)
    provider_to_canonical = {
        str(country["eurostat_code"]): str(canonical_code)
        for canonical_code, country in countries.items()
    }
    quarterly = parse_job_vacancy_response(
        downloaded.content,
        country_mapping=provider_to_canonical,
        request_url=downloaded.request_url,
        retrieved_at_utc=downloaded.retrieved_at_utc,
        sha256=downloaded.sha256,
        dataset_code=str(indicator["dataset"]),
    )

    expected_rows = len(countries) * len(
        pd.period_range(start=start_period, end=end_period, freq="Q")
    )
    summary: dict[str, object] = {
        "indicator_id": "JOB_VACANCY_RATE",
        "provider": "Eurostat",
        "dataset_code": str(indicator["dataset"]),
        "classification_version": "NACE Rev. 2",
        "activity_scope": "B-S",
        "requested_period_start": start_period,
        "requested_period_end": end_period,
        "expected_quarterly_observations": expected_rows,
        "returned_quarterly_rows": int(len(quarterly)),
        "available_quarterly_values": int(quarterly["value"].notna().sum()),
        "missing_quarterly_values": int(quarterly["value"].isna().sum()),
        "provisional_values": int(quarterly["is_provisional"].sum()),
        "italy_coverage_warning_rows": int(
            quarterly["coverage_note_code"]
            .eq("ITALY_REDUCED_PUBLIC_SECTOR_COVERAGE")
            .sum()
        ),
        "flash_publication_lag_days": 50,
        "fuller_publication_lag_days": 78,
        "revision_treatment": "current_vintage_at_retrieval_time",
        "retrieved_at_utc": downloaded.retrieved_at_utc,
        "request_url": downloaded.request_url,
        "raw_sha256": downloaded.sha256,
        "provider_dataset_updated_at": (
            str(quarterly["provider_dataset_updated_at"].iloc[0])
            if len(quarterly)
            else ""
        ),
    }
    timestamp = downloaded.retrieved_at_utc.replace(":", "").replace("-", "")
    raw_name = f"job_vacancy_{timestamp}_{downloaded.sha256[:12]}.json"
    summary["raw_response_file"] = str(raw_dir / raw_name)
    atomic_write_bytes(raw_dir / raw_name, downloaded.content)
    atomic_write_csv(canonical_dir / "job_vacancy_quarterly.csv", quarterly)
    atomic_write_bytes(
        output_dir / "job_vacancy_ingestion_summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return JobVacancyIngestionResult(quarterly=quarterly, summary=summary)
