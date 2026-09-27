"""World Bank Indicators API adapter for approved annual inflation data."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

import httpx
import pandas as pd

from asteria_retention.adapters.http_retry import (
    SourceRequestError,
    get_with_bounded_retry,
)


WORLD_BANK_API_ROOT = "https://api.worldbank.org/v2"
INFLATION_INDICATOR_CODE = "FP.CPI.TOTL.ZG"


class WorldBankSourceError(RuntimeError):
    """Raised when the World Bank source cannot satisfy its contract."""


@dataclass(frozen=True)
class WorldBankDownload:
    content: bytes
    request_url: str
    retrieved_at_utc: str
    sha256: str


def build_inflation_url(
    countries: Mapping[str, Mapping[str, str]],
    *,
    start_year: int,
    end_year: int,
) -> str:
    provider_codes = ";".join(
        str(country["world_bank_code"]) for country in countries.values()
    )
    base = (
        f"{WORLD_BANK_API_ROOT}/country/{provider_codes}/indicator/"
        f"{INFLATION_INDICATOR_CODE}"
    )
    return str(
        httpx.URL(
            base,
            params={
                "date": f"{start_year}:{end_year}",
                "format": "json",
                "per_page": "100",
            },
        )
    )


def download_world_bank_json(
    url: str, *, timeout_seconds: float = 30.0
) -> WorldBankDownload:
    try:
        response = get_with_bounded_retry(
            url,
            source_name="World Bank",
            timeout_seconds=timeout_seconds,
        )
    except SourceRequestError as exc:
        raise WorldBankSourceError(str(exc)) from exc

    content = response.content
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    return WorldBankDownload(
        content=content,
        request_url=str(response.url),
        retrieved_at_utc=retrieved,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def parse_inflation_response(
    content: bytes,
    *,
    country_mapping: Mapping[str, str],
    start_year: int,
    end_year: int,
    request_url: str,
    retrieved_at_utc: str,
    sha256: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorldBankSourceError("World Bank response is not valid JSON") from exc

    if not isinstance(payload, list) or len(payload) != 2:
        raise WorldBankSourceError("World Bank response must contain metadata and data")
    metadata, observations = payload
    if not isinstance(metadata, dict) or not isinstance(observations, list):
        raise WorldBankSourceError("World Bank response structure is invalid")

    indexed: dict[tuple[str, int], dict[str, object]] = {}
    for observation in observations:
        if not isinstance(observation, dict):
            raise WorldBankSourceError("World Bank observation is not an object")
        indicator = observation.get("indicator")
        indicator_id = indicator.get("id") if isinstance(indicator, dict) else None
        if indicator_id != INFLATION_INDICATOR_CODE:
            raise WorldBankSourceError(
                f"unexpected World Bank indicator code: {indicator_id!r}"
            )
        provider_country = str(observation.get("countryiso3code", ""))
        if provider_country not in country_mapping:
            raise WorldBankSourceError(
                f"unmapped World Bank country code: {provider_country}"
            )
        try:
            year = int(str(observation.get("date")))
        except ValueError as exc:
            raise WorldBankSourceError("World Bank observation has an invalid year") from exc
        indexed[(provider_country, year)] = observation

    records: list[dict[str, object]] = []
    for provider_country, canonical_country in country_mapping.items():
        for year in range(start_year, end_year + 1):
            observation = indexed.get((provider_country, year), {})
            country = observation.get("country")
            country_name = country.get("value", "") if isinstance(country, dict) else ""
            records.append(
                {
                    "indicator_id": "CONSUMER_PRICE_INFLATION",
                    "indicator_code": INFLATION_INDICATOR_CODE,
                    "indicator_name": "Inflation, consumer prices (annual %)",
                    "provider": "World Bank",
                    "source_id": str(metadata.get("sourceid", "")),
                    "source_name": "World Development Indicators",
                    "source_organization": (
                        "International Financial Statistics database, "
                        "International Monetary Fund (IMF)"
                    ),
                    "provider_country_code": provider_country,
                    "country_code": canonical_country,
                    "country_name": str(country_name),
                    "reference_year": year,
                    "value": observation.get("value"),
                    "unit_description": "annual_percent_change",
                    "native_frequency": "annual",
                    "observation_status": str(observation.get("obs_status", "")),
                    "provider_last_updated": str(metadata.get("lastupdated", "")),
                    "retrieved_at_utc": retrieved_at_utc,
                    "request_url": request_url,
                    "raw_sha256": sha256,
                    "license": "CC BY 4.0",
                    "attribution": (
                        "World Bank, World Development Indicators, Inflation, consumer "
                        "prices (annual %) (FP.CPI.TOTL.ZG); underlying source: "
                        "International Financial Statistics database, IMF."
                    ),
                    "transformation_note": (
                        "Provider annual value retained; not expanded to quarters or months."
                    ),
                }
            )

    frame = pd.DataFrame(records)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.sort_values(
        ["country_code", "reference_year"], kind="stable"
    ).reset_index(drop=True)
    response_metadata: dict[str, object] = {
        "source_id": str(metadata.get("sourceid", "")),
        "last_updated": str(metadata.get("lastupdated", "")),
        "api_reported_total": int(metadata.get("total", 0)),
        "api_pages": int(metadata.get("pages", 0)),
        "source_observations_returned": len(observations),
    }
    return frame, response_metadata
