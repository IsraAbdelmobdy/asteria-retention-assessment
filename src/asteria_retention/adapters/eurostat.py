"""Small Eurostat JSON-stat adapter for the approved external series."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

import httpx
import pandas as pd

from asteria_retention.adapters.http_retry import (
    SourceRequestError,
    get_with_bounded_retry,
)


EUROSTAT_API_ROOT = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
)


class EurostatSourceError(RuntimeError):
    """Raised when Eurostat cannot be fetched or violates the source contract."""


@dataclass(frozen=True)
class EurostatDownload:
    content: bytes
    request_url: str
    retrieved_at_utc: str
    sha256: str


def build_unemployment_url(
    indicator_config: Mapping[str, Any],
    countries: Mapping[str, Mapping[str, str]],
    *,
    start_period: str,
    end_period: str,
) -> str:
    return _build_indicator_url(
        indicator_config,
        countries,
        start_period=start_period,
        end_period=end_period,
    )


def build_job_vacancy_url(
    indicator_config: Mapping[str, Any],
    countries: Mapping[str, Mapping[str, str]],
    *,
    start_period: str,
    end_period: str,
) -> str:
    return _build_indicator_url(
        indicator_config,
        countries,
        start_period=start_period,
        end_period=end_period,
    )


def _build_indicator_url(
    indicator_config: Mapping[str, Any],
    countries: Mapping[str, Mapping[str, str]],
    *,
    start_period: str,
    end_period: str,
) -> str:
    dataset = str(indicator_config["dataset"])
    parameters: list[tuple[str, str]] = [("lang", "en")]
    parameters.extend(
        (str(key), str(value))
        for key, value in indicator_config["parameters"].items()
    )
    parameters.extend(
        ("geo", str(country["eurostat_code"])) for country in countries.values()
    )
    parameters.extend(
        [("sinceTimePeriod", start_period), ("untilTimePeriod", end_period)]
    )
    return str(httpx.URL(f"{EUROSTAT_API_ROOT}/{dataset}", params=parameters))


def download_eurostat_json(url: str, *, timeout_seconds: float = 30.0) -> EurostatDownload:
    try:
        response = get_with_bounded_retry(
            url,
            source_name="Eurostat",
            timeout_seconds=timeout_seconds,
        )
    except SourceRequestError as exc:
        raise EurostatSourceError(str(exc)) from exc

    content = response.content
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    return EurostatDownload(
        content=content,
        request_url=str(response.url),
        retrieved_at_utc=retrieved,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def _category_positions(dimension: Mapping[str, Any], name: str) -> dict[str, int]:
    try:
        index = dimension["category"]["index"]
    except (KeyError, TypeError) as exc:
        raise EurostatSourceError(f"missing category index for dimension {name}") from exc
    if isinstance(index, dict):
        return {str(code): int(position) for code, position in index.items()}
    if isinstance(index, list):
        return {str(code): position for position, code in enumerate(index)}
    raise EurostatSourceError(f"unsupported category index for dimension {name}")


def _indexed_value(values: object, position: int) -> object:
    if isinstance(values, list):
        return values[position] if position < len(values) else None
    if isinstance(values, dict):
        return values.get(str(position))
    return None


def parse_unemployment_response(
    content: bytes,
    *,
    country_mapping: Mapping[str, str],
    request_url: str,
    retrieved_at_utc: str,
    sha256: str,
    dataset_code: str,
) -> pd.DataFrame:
    frame = _parse_selected_country_time_response(
        content,
        country_mapping=country_mapping,
        request_url=request_url,
        retrieved_at_utc=retrieved_at_utc,
        sha256=sha256,
        dataset_code=dataset_code,
    )
    periods = pd.PeriodIndex(frame["reference_period"], freq="M")
    frame["indicator_id"] = "UNEMPLOYMENT_RATE"
    frame["period_start"] = periods.start_time.strftime("%Y-%m-%d")
    frame["period_end"] = periods.end_time.strftime("%Y-%m-%d")
    frame["unit_code"] = "PC_ACT"
    frame["native_frequency"] = "monthly"
    frame["seasonal_adjustment"] = "SA"
    frame["age_code"] = "TOTAL"
    frame["sex_code"] = "T"
    columns = [
        "indicator_id",
        "provider",
        "dataset_code",
        "provider_country_code",
        "country_code",
        "reference_period",
        "period_start",
        "period_end",
        "value",
        "unit_code",
        "native_frequency",
        "seasonal_adjustment",
        "age_code",
        "sex_code",
        "observation_status",
        "provider_dataset_updated_at",
        "retrieved_at_utc",
        "request_url",
        "raw_sha256",
    ]
    return frame.loc[:, columns]


def parse_job_vacancy_response(
    content: bytes,
    *,
    country_mapping: Mapping[str, str],
    request_url: str,
    retrieved_at_utc: str,
    sha256: str,
    dataset_code: str,
) -> pd.DataFrame:
    frame = _parse_selected_country_time_response(
        content,
        country_mapping=country_mapping,
        request_url=request_url,
        retrieved_at_utc=retrieved_at_utc,
        sha256=sha256,
        dataset_code=dataset_code,
    )
    periods = pd.PeriodIndex(
        frame["reference_period"].str.replace("-Q", "Q", regex=False), freq="Q"
    )
    frame["indicator_id"] = "JOB_VACANCY_RATE"
    frame["quarter_start"] = periods.start_time.strftime("%Y-%m-%d")
    frame["quarter_end"] = periods.end_time.strftime("%Y-%m-%d")
    frame["unit_description"] = "percent_of_total_posts"
    frame["native_frequency"] = "quarterly"
    frame["seasonal_adjustment"] = "SA"
    frame["activity_scope"] = "B-S"
    frame["size_class"] = "TOTAL"
    frame["is_provisional"] = frame["observation_status"].str.contains(
        "p", case=False, na=False
    )
    italy = frame["country_code"].eq("IT")
    frame["coverage_note_code"] = ""
    frame.loc[italy, "coverage_note_code"] = (
        "ITALY_REDUCED_PUBLIC_SECTOR_COVERAGE"
    )
    frame["coverage_note"] = ""
    frame.loc[italy, "coverage_note"] = (
        "Public administration is not surveyed and public institutions are not "
        "fully covered in education and health; cross-country comparability is reduced."
    )
    frame["flash_publication_lag_days"] = 50
    frame["fuller_publication_lag_days"] = 78
    frame["availability_note"] = (
        "Retrospective current-vintage value; flash estimates are typically released "
        "around 50 days and fuller results around 78 days after quarter end."
    )
    columns = [
        "indicator_id",
        "provider",
        "dataset_code",
        "provider_country_code",
        "country_code",
        "reference_period",
        "quarter_start",
        "quarter_end",
        "value",
        "unit_description",
        "native_frequency",
        "seasonal_adjustment",
        "activity_scope",
        "size_class",
        "observation_status",
        "is_provisional",
        "coverage_note_code",
        "coverage_note",
        "flash_publication_lag_days",
        "fuller_publication_lag_days",
        "availability_note",
        "provider_dataset_updated_at",
        "retrieved_at_utc",
        "request_url",
        "raw_sha256",
    ]
    return frame.loc[:, columns]


def _parse_selected_country_time_response(
    content: bytes,
    *,
    country_mapping: Mapping[str, str],
    request_url: str,
    retrieved_at_utc: str,
    sha256: str,
    dataset_code: str,
) -> pd.DataFrame:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EurostatSourceError("Eurostat response is not valid JSON") from exc

    dimension_ids = payload.get("id")
    dimension_sizes = payload.get("size")
    dimensions = payload.get("dimension")
    if not isinstance(dimension_ids, list) or not isinstance(dimension_sizes, list):
        raise EurostatSourceError("Eurostat response is missing JSON-stat dimensions")
    if len(dimension_ids) != len(dimension_sizes) or not isinstance(dimensions, dict):
        raise EurostatSourceError("Eurostat JSON-stat dimensions are inconsistent")
    if "geo" not in dimension_ids or "time" not in dimension_ids:
        raise EurostatSourceError("Eurostat response must contain geo and time dimensions")

    for dimension_id, size in zip(dimension_ids, dimension_sizes, strict=True):
        if dimension_id not in {"geo", "time"} and int(size) != 1:
            raise EurostatSourceError(
                f"expected one selected value for dimension {dimension_id}, got {size}"
            )

    geo_positions = _category_positions(dimensions["geo"], "geo")
    time_positions = _category_positions(dimensions["time"], "time")
    values = payload.get("value")
    statuses = payload.get("status")
    updated = str(payload.get("updated", ""))
    records: list[dict[str, object]] = []

    for provider_country, geo_position in sorted(
        geo_positions.items(), key=lambda item: item[1]
    ):
        if provider_country not in country_mapping:
            raise EurostatSourceError(
                f"unmapped Eurostat country code: {provider_country}"
            )
        for reference_period, time_position in sorted(
            time_positions.items(), key=lambda item: item[1]
        ):
            coordinates = {dimension_id: 0 for dimension_id in dimension_ids}
            coordinates["geo"] = geo_position
            coordinates["time"] = time_position
            flat_position = 0
            for dimension_id, size in zip(
                dimension_ids, dimension_sizes, strict=True
            ):
                flat_position = flat_position * int(size) + coordinates[dimension_id]

            value = _indexed_value(values, flat_position)
            status = _indexed_value(statuses, flat_position)
            records.append(
                {
                    "provider": "Eurostat",
                    "dataset_code": dataset_code,
                    "provider_country_code": provider_country,
                    "country_code": country_mapping[provider_country],
                    "reference_period": str(reference_period),
                    "value": value,
                    "observation_status": "" if status is None else str(status),
                    "provider_dataset_updated_at": updated,
                    "retrieved_at_utc": retrieved_at_utc,
                    "request_url": request_url,
                    "raw_sha256": sha256,
                }
            )

    frame = pd.DataFrame(records)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.sort_values(
        ["country_code", "reference_period"], kind="stable"
    ).reset_index(drop=True)
