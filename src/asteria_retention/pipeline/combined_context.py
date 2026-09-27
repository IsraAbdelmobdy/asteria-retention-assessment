"""Build temporally aligned workforce and external-context outputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asteria_retention.domain.alignment import (
    build_annual_inflation_context,
    build_quarterly_context,
)
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv


class CombinedContextError(RuntimeError):
    """Raised when required prepared inputs for alignment are unavailable."""


@dataclass(frozen=True)
class CombinedContextResult:
    quarterly: pd.DataFrame
    annual: pd.DataFrame
    summary: dict[str, object]


def build_combined_context(
    canonical_dir: Path,
    output_dir: Path,
) -> CombinedContextResult:
    paths = {
        "new_hire": output_dir / "new_hire_6m_retention.csv",
        "senior_hire": output_dir / "senior_hire_12m_retention.csv",
        "turnover": output_dir / "regretted_turnover_12m.csv",
        "unemployment_monthly": canonical_dir / "unemployment_monthly.csv",
        "unemployment_quarterly": output_dir / "unemployment_quarterly.csv",
        "job_vacancy_quarterly": canonical_dir / "job_vacancy_quarterly.csv",
        "inflation_annual": canonical_dir / "consumer_price_inflation_annual.csv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise CombinedContextError(
            "required prepared files are missing: " + ", ".join(missing)
        )

    try:
        frames = {name: pd.read_csv(path) for name, path in paths.items()}
        quarterly = build_quarterly_context(
            frames["new_hire"],
            frames["senior_hire"],
            frames["turnover"],
            frames["unemployment_monthly"],
            frames["unemployment_quarterly"],
            frames["job_vacancy_quarterly"],
        )
        annual = build_annual_inflation_context(
            frames["new_hire"],
            frames["senior_hire"],
            frames["turnover"],
            frames["inflation_annual"],
        )
    except (KeyError, ValueError, pd.errors.ParserError) as exc:
        raise CombinedContextError(f"combined context build failed: {exc}") from exc

    turnover_rows = quarterly["objective_id"].eq("REGRETTED_TURNOVER_12M")
    incomplete_turnover = turnover_rows & (
        quarterly["unemployment_coverage_status"].ne("COMPLETE")
        | quarterly["job_vacancy_coverage_status"].ne("COMPLETE")
    )
    incomplete_country_periods = quarterly.loc[
        incomplete_turnover, ["country_code", "period"]
    ].drop_duplicates()
    complete_turnover_periods = sorted(
        quarterly.loc[
            turnover_rows & ~incomplete_turnover, "period"
        ].drop_duplicates()
    )
    summary: dict[str, object] = {
        "quarterly_rows": int(len(quarterly)),
        "annual_rows": int(len(annual)),
        "quarterly_small_sample_warnings": int(
            quarterly["sample_warning"].fillna("").ne("").sum()
        ),
        "annual_small_sample_warnings": int(
            annual["sample_warning"].fillna("").ne("").sum()
        ),
        "incomplete_trailing_external_country_quarters": int(
            len(incomplete_country_periods)
        ),
        "first_complete_trailing_external_period": (
            complete_turnover_periods[0] if complete_turnover_periods else None
        ),
        "inflation_missing_rows": int(
            annual["inflation_coverage_status"].eq("MISSING").sum()
        ),
        "quarterly_output": str(output_dir / "combined_quarterly_context.csv"),
        "annual_output": str(output_dir / "combined_annual_inflation_context.csv"),
    }
    atomic_write_csv(output_dir / "combined_quarterly_context.csv", quarterly)
    atomic_write_csv(output_dir / "combined_annual_inflation_context.csv", annual)
    atomic_write_bytes(
        output_dir / "combined_context_summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return CombinedContextResult(quarterly=quarterly, annual=annual, summary=summary)
