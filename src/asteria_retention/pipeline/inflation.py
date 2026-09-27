"""Download and preserve annual World Bank consumer-price inflation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asteria_retention.adapters.world_bank import (
    INFLATION_INDICATOR_CODE,
    WorldBankDownload,
    WorldBankSourceError,
    build_inflation_url,
    download_world_bank_json,
    parse_inflation_response,
)
from asteria_retention.config import load_project_config
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv


@dataclass(frozen=True)
class InflationIngestionResult:
    annual: pd.DataFrame
    summary: dict[str, object]


def ingest_inflation(
    project_root: Path,
    raw_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    *,
    download: WorldBankDownload | None = None,
) -> InflationIngestionResult:
    config = load_project_config(project_root)["indicators"]
    analysis = config["analysis"]
    countries = config["countries"]
    indicator = config["indicators"]["consumer_price_inflation"]
    if str(indicator["indicator_code"]) != INFLATION_INDICATOR_CODE:
        raise WorldBankSourceError(
            f"approved inflation contract requires {INFLATION_INDICATOR_CODE}"
        )

    start_year = int(str(analysis["start_date"])[:4])
    end_year = int(str(analysis["end_date"])[:4])
    url = build_inflation_url(countries, start_year=start_year, end_year=end_year)
    downloaded = download or download_world_bank_json(url)
    provider_to_canonical = {
        str(country["world_bank_code"]): str(canonical_code)
        for canonical_code, country in countries.items()
    }
    annual, response_metadata = parse_inflation_response(
        downloaded.content,
        country_mapping=provider_to_canonical,
        start_year=start_year,
        end_year=end_year,
        request_url=downloaded.request_url,
        retrieved_at_utc=downloaded.retrieved_at_utc,
        sha256=downloaded.sha256,
    )

    expected_rows = len(countries) * (end_year - start_year + 1)
    summary: dict[str, object] = {
        "indicator_id": "CONSUMER_PRICE_INFLATION",
        "indicator_code": INFLATION_INDICATOR_CODE,
        "provider": "World Bank",
        "source_id": response_metadata["source_id"],
        "source_name": "World Development Indicators",
        "source_organization": (
            "International Financial Statistics database, International Monetary "
            "Fund (IMF)"
        ),
        "license": "CC BY 4.0",
        "requested_year_start": start_year,
        "requested_year_end": end_year,
        "expected_annual_observations": expected_rows,
        "canonical_annual_rows": int(len(annual)),
        "source_observations_returned": response_metadata[
            "source_observations_returned"
        ],
        "available_annual_values": int(annual["value"].notna().sum()),
        "missing_annual_values": int(annual["value"].isna().sum()),
        "provider_last_updated": response_metadata["last_updated"],
        "revision_treatment": "current_vintage_at_retrieval_time",
        "frequency_treatment": "annual_values_not_expanded",
        "retrieved_at_utc": downloaded.retrieved_at_utc,
        "request_url": downloaded.request_url,
        "raw_sha256": downloaded.sha256,
        "attribution": (
            "World Bank, World Development Indicators, Inflation, consumer prices "
            "(annual %) (FP.CPI.TOTL.ZG); underlying source: International Financial "
            "Statistics database, IMF. Licensed under CC BY 4.0."
        ),
    }
    timestamp = downloaded.retrieved_at_utc.replace(":", "").replace("-", "")
    raw_name = f"inflation_{timestamp}_{downloaded.sha256[:12]}.json"
    summary["raw_response_file"] = str(raw_dir / raw_name)
    atomic_write_bytes(raw_dir / raw_name, downloaded.content)
    atomic_write_csv(canonical_dir / "consumer_price_inflation_annual.csv", annual)
    atomic_write_bytes(
        output_dir / "inflation_ingestion_summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return InflationIngestionResult(annual=annual, summary=summary)
