"""One-command orchestration for the complete local analytical workflow."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

import pandas as pd

from asteria_retention.adapters.eurostat import EurostatDownload
from asteria_retention.adapters.workforce_csv import load_supplied_data
from asteria_retention.adapters.world_bank import WorldBankDownload
from asteria_retention.config import load_project_config
from asteria_retention.domain.external import aggregate_monthly_unemployment_to_quarters
from asteria_retention.pipeline.association_analysis import build_association_analysis
from asteria_retention.pipeline.combined_context import build_combined_context
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv
from asteria_retention.pipeline.inflation import ingest_inflation
from asteria_retention.pipeline.job_vacancy import ingest_job_vacancy
from asteria_retention.pipeline.new_hire_retention import (
    prepare_new_hire_six_month_retention,
)
from asteria_retention.pipeline.regretted_turnover import (
    prepare_regretted_turnover_twelve_month,
)
from asteria_retention.pipeline.senior_hire_retention import (
    prepare_senior_hire_twelve_month_retention,
)
from asteria_retention.pipeline.unemployment import ingest_unemployment
from asteria_retention.pipeline.workforce_quality import prepare_workforce
from asteria_retention.storage.duckdb_store import build_database


class CorePipelineError(RuntimeError):
    """Raised with the name of the core stage that could not complete."""


@dataclass(frozen=True)
class CorePipelineResult:
    mode: str
    completed_stages: tuple[str, ...]
    database_path: Path
    summary_path: Path


T = TypeVar("T")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _write_summary(output_dir: Path, summary: dict[str, object]) -> Path:
    path = output_dir / "core_run_summary.json"
    atomic_write_bytes(
        path,
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return path


def _validate_complete_grid(
    frame: pd.DataFrame,
    *,
    name: str,
    period_column: str,
    expected_countries: set[str],
    expected_periods: set[str] | set[int],
) -> None:
    required = {"country_code", period_column, "value"}
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{name} is missing columns: {', '.join(sorted(missing_columns))}"
        )
    keys = frame[["country_code", period_column]]
    if keys.duplicated().any():
        raise ValueError(f"{name} contains duplicate country-period rows")
    actual = set(map(tuple, keys.itertuples(index=False, name=None)))
    expected = {
        (country, period)
        for country in expected_countries
        for period in expected_periods
    }
    missing = expected.difference(actual)
    unexpected = actual.difference(expected)
    if missing or unexpected:
        raise ValueError(
            f"{name} does not match its configured country-period grid: "
            f"{len(missing)} missing and {len(unexpected)} unexpected rows"
        )


def prepare_offline_external_data(
    project_root: Path,
    raw_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
) -> str:
    """Validate cached canonical external data and rebuild derived unemployment."""
    indicator_config = load_project_config(project_root)["indicators"]
    analysis = indicator_config["analysis"]
    countries = set(map(str, indicator_config["countries"]))
    indicators = indicator_config["indicators"]

    paths = {
        "unemployment": canonical_dir / "unemployment_monthly.csv",
        "job vacancies": canonical_dir / "job_vacancy_quarterly.csv",
        "inflation": canonical_dir / "consumer_price_inflation_annual.csv",
    }
    missing_files = [str(path) for path in paths.values() if not path.is_file()]
    offline_source = "CACHED_CANONICAL"
    if missing_files:
        fixture_dir = project_root / "tests" / "fixtures" / "replay"
        manifest_path = fixture_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError(
                "offline mode found neither complete prepared external data nor "
                f"the replay manifest: {manifest_path}"
            )
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            declarations = manifest["fixtures"]
            storage_normalization = manifest.get("storage_normalization")
            payloads: dict[str, tuple[bytes, dict[str, object]]] = {}
            for name in ("unemployment", "job_vacancy", "inflation"):
                declaration = declarations[name]
                fixture_path = fixture_dir / str(declaration["file"])
                content = fixture_path.read_bytes()
                if (
                    storage_normalization
                    == "remove_one_trailing_lf_before_checksum_and_replay"
                    and content.endswith(b"\n")
                ):
                    content = content[:-1]
                actual_sha256 = hashlib.sha256(content).hexdigest()
                expected_sha256 = str(declaration["sha256"])
                if actual_sha256 != expected_sha256:
                    raise ValueError(
                        f"replay fixture checksum mismatch: {fixture_path}"
                    )
                payloads[name] = (content, declaration)
        except (KeyError, TypeError, json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"invalid replay fixture contract: {exc}") from exc

        unemployment_content, unemployment_meta = payloads["unemployment"]
        vacancy_content, vacancy_meta = payloads["job_vacancy"]
        inflation_content, inflation_meta = payloads["inflation"]
        ingest_unemployment(
            project_root,
            raw_dir / "eurostat",
            canonical_dir,
            output_dir,
            download=EurostatDownload(
                content=unemployment_content,
                request_url=str(unemployment_meta["request_url"]),
                retrieved_at_utc=str(unemployment_meta["retrieved_at_utc"]),
                sha256=str(unemployment_meta["sha256"]),
            ),
        )
        ingest_job_vacancy(
            project_root,
            raw_dir / "eurostat",
            canonical_dir,
            output_dir,
            download=EurostatDownload(
                content=vacancy_content,
                request_url=str(vacancy_meta["request_url"]),
                retrieved_at_utc=str(vacancy_meta["retrieved_at_utc"]),
                sha256=str(vacancy_meta["sha256"]),
            ),
        )
        ingest_inflation(
            project_root,
            raw_dir / "world_bank",
            canonical_dir,
            output_dir,
            download=WorldBankDownload(
                content=inflation_content,
                request_url=str(inflation_meta["request_url"]),
                retrieved_at_utc=str(inflation_meta["retrieved_at_utc"]),
                sha256=str(inflation_meta["sha256"]),
            ),
        )
        offline_source = "REPLAY_FIXTURES"

    unemployment = pd.read_csv(paths["unemployment"], dtype={"reference_period": str})
    vacancy = pd.read_csv(paths["job vacancies"], dtype={"reference_period": str})
    inflation = pd.read_csv(paths["inflation"])

    unemployment_start = str(
        indicators["unemployment_rate"].get(
            "ingestion_start", str(analysis["start_date"])[:7]
        )
    )
    unemployment_end = str(analysis["end_date"])[:7]
    _validate_complete_grid(
        unemployment,
        name="cached unemployment",
        period_column="reference_period",
        expected_countries=countries,
        expected_periods=set(
            pd.period_range(unemployment_start, unemployment_end, freq="M").astype(str)
        ),
    )

    vacancy_start = str(
        indicators["job_vacancy_rate"].get(
            "ingestion_start", f"{str(analysis['start_date'])[:4]}-Q1"
        )
    )
    vacancy_end = f"{str(analysis['end_date'])[:4]}-Q4"
    vacancy_periods = {
        f"{period.year}-Q{period.quarter}"
        for period in pd.period_range(vacancy_start, vacancy_end, freq="Q")
    }
    _validate_complete_grid(
        vacancy,
        name="cached job vacancies",
        period_column="reference_period",
        expected_countries=countries,
        expected_periods=vacancy_periods,
    )

    start_year = int(str(analysis["start_date"])[:4])
    end_year = int(str(analysis["end_date"])[:4])
    _validate_complete_grid(
        inflation,
        name="cached inflation",
        period_column="reference_year",
        expected_countries=countries,
        expected_periods=set(range(start_year, end_year + 1)),
    )
    quarterly = aggregate_monthly_unemployment_to_quarters(unemployment)
    atomic_write_csv(output_dir / "unemployment_quarterly.csv", quarterly)
    return offline_source


def run_core_pipeline(
    *,
    project_root: Path,
    input_dir: Path,
    raw_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    database_path: Path,
    offline: bool,
    progress: Callable[[str], None] | None = None,
) -> CorePipelineResult:
    mode = "OFFLINE" if offline else "ONLINE"
    started_at = _utc_now()
    completed: list[str] = []
    summary: dict[str, object] = {
        "mode": mode,
        "status": "RUNNING",
        "started_at_utc": started_at,
        "completed_stages": completed,
        "database_path": str(database_path),
    }

    def execute(name: str, action: Callable[[], T]) -> T:
        if progress is not None:
            progress(name)
        try:
            result = action()
        except Exception as exc:
            summary.update(
                {
                    "status": "FAILED",
                    "failed_stage": name,
                    "error": str(exc),
                    "completed_at_utc": _utc_now(),
                }
            )
            _write_summary(output_dir, summary)
            raise CorePipelineError(f"stage '{name}' failed: {exc}") from exc
        completed.append(name)
        return result

    execute("validate_configuration", lambda: load_project_config(project_root))
    supplied = execute("verify_supplied_inputs", lambda: load_supplied_data(input_dir))
    quality = execute(
        "prepare_workforce",
        lambda: prepare_workforce(
            input_dir, canonical_dir, output_dir, supplied=supplied
        ),
    )
    execute(
        "calculate_new_hire_retention",
        lambda: prepare_new_hire_six_month_retention(
            input_dir,
            canonical_dir,
            output_dir,
            quality_result=quality,
            supplied=supplied,
        ),
    )
    execute(
        "calculate_senior_hire_retention",
        lambda: prepare_senior_hire_twelve_month_retention(
            input_dir,
            canonical_dir,
            output_dir,
            quality_result=quality,
            supplied=supplied,
        ),
    )
    execute(
        "calculate_regretted_turnover",
        lambda: prepare_regretted_turnover_twelve_month(
            input_dir,
            canonical_dir,
            output_dir,
            quality_result=quality,
            supplied=supplied,
        ),
    )

    if offline:
        offline_source = execute(
            "validate_cached_external_data",
            lambda: prepare_offline_external_data(
                project_root, raw_dir, canonical_dir, output_dir
            ),
        )
        summary["offline_external_source"] = offline_source
    else:
        execute(
            "ingest_unemployment",
            lambda: ingest_unemployment(
                project_root,
                raw_dir / "eurostat",
                canonical_dir,
                output_dir,
            ),
        )
        execute(
            "ingest_job_vacancy",
            lambda: ingest_job_vacancy(
                project_root,
                raw_dir / "eurostat",
                canonical_dir,
                output_dir,
            ),
        )
        execute(
            "ingest_inflation",
            lambda: ingest_inflation(
                project_root,
                raw_dir / "world_bank",
                canonical_dir,
                output_dir,
            ),
        )

    execute(
        "build_combined_context",
        lambda: build_combined_context(canonical_dir, output_dir),
    )
    execute(
        "analyze_associations", lambda: build_association_analysis(output_dir)
    )
    execute(
        "build_database",
        lambda: build_database(canonical_dir, output_dir, database_path),
    )
    summary.update(
        {
            "status": "SUCCEEDED",
            "completed_at_utc": _utc_now(),
            "completed_stages": completed,
        }
    )
    summary_path = _write_summary(output_dir, summary)
    return CorePipelineResult(
        mode=mode,
        completed_stages=tuple(completed),
        database_path=database_path,
        summary_path=summary_path,
    )
