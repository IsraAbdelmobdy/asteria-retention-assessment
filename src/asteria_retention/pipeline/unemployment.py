"""Download, preserve, canonicalise, and aggregate Eurostat unemployment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asteria_retention.adapters.eurostat import (
    EurostatDownload,
    build_unemployment_url,
    download_eurostat_json,
    parse_unemployment_response,
)
from asteria_retention.config import load_project_config
from asteria_retention.domain.external import aggregate_monthly_unemployment_to_quarters
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv


@dataclass(frozen=True)
class UnemploymentIngestionResult:
    monthly: pd.DataFrame
    quarterly: pd.DataFrame
    summary: dict[str, object]


def ingest_unemployment(
    project_root: Path,
    raw_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    *,
    download: EurostatDownload | None = None,
) -> UnemploymentIngestionResult:
    config = load_project_config(project_root)["indicators"]
    analysis = config["analysis"]
    countries = config["countries"]
    indicator = config["indicators"]["unemployment_rate"]
    start_period = str(
        indicator.get("ingestion_start", str(analysis["start_date"])[:7])
    )
    end_period = str(analysis["end_date"])[:7]
    url = build_unemployment_url(
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
    monthly = parse_unemployment_response(
        downloaded.content,
        country_mapping=provider_to_canonical,
        request_url=downloaded.request_url,
        retrieved_at_utc=downloaded.retrieved_at_utc,
        sha256=downloaded.sha256,
        dataset_code=str(indicator["dataset"]),
    )
    quarterly = aggregate_monthly_unemployment_to_quarters(monthly)

    expected_monthly = len(countries) * len(
        pd.period_range(start=start_period, end=end_period, freq="M")
    )
    expected_quarterly = len(countries) * len(
        pd.period_range(start=start_period, end=end_period, freq="Q")
    )
    summary: dict[str, object] = {
        "indicator_id": "UNEMPLOYMENT_RATE",
        "provider": "Eurostat",
        "dataset_code": str(indicator["dataset"]),
        "requested_period_start": start_period,
        "requested_period_end": end_period,
        "expected_monthly_observations": expected_monthly,
        "returned_monthly_rows": int(len(monthly)),
        "available_monthly_values": int(monthly["value"].notna().sum()),
        "missing_monthly_values": int(monthly["value"].isna().sum()),
        "expected_quarterly_observations": expected_quarterly,
        "returned_quarterly_rows": int(len(quarterly)),
        "complete_quarters": int(quarterly["coverage_status"].eq("COMPLETE").sum()),
        "incomplete_quarters": int(
            quarterly["coverage_status"].eq("INCOMPLETE").sum()
        ),
        "typical_publication_lag_days": 31,
        "revision_treatment": "current_vintage_at_retrieval_time",
        "retrieved_at_utc": downloaded.retrieved_at_utc,
        "request_url": downloaded.request_url,
        "raw_sha256": downloaded.sha256,
        "provider_dataset_updated_at": (
            str(monthly["provider_dataset_updated_at"].iloc[0]) if len(monthly) else ""
        ),
    }

    timestamp = downloaded.retrieved_at_utc.replace(":", "").replace("-", "")
    raw_name = f"unemployment_{timestamp}_{downloaded.sha256[:12]}.json"
    summary["raw_response_file"] = str(raw_dir / raw_name)
    atomic_write_bytes(raw_dir / raw_name, downloaded.content)
    atomic_write_csv(canonical_dir / "unemployment_monthly.csv", monthly)
    atomic_write_csv(output_dir / "unemployment_quarterly.csv", quarterly)
    atomic_write_bytes(
        output_dir / "unemployment_ingestion_summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    return UnemploymentIngestionResult(
        monthly=monthly, quarterly=quarterly, summary=summary
    )
