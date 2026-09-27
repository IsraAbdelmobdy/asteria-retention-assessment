"""Build the approved association-analysis artifact."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from asteria_retention.domain.association import build_association_results
from asteria_retention.pipeline.files import atomic_write_bytes, atomic_write_csv


class AssociationAnalysisError(RuntimeError):
    """Raised when association inputs are unavailable or invalid."""


@dataclass(frozen=True)
class AssociationAnalysisResult:
    associations: pd.DataFrame
    summary: dict[str, object]


def build_association_analysis(output_dir: Path) -> AssociationAnalysisResult:
    quarterly_path = output_dir / "combined_quarterly_context.csv"
    annual_path = output_dir / "combined_annual_inflation_context.csv"
    missing = [str(path) for path in (quarterly_path, annual_path) if not path.is_file()]
    if missing:
        raise AssociationAnalysisError(
            "required combined-context files are missing: " + ", ".join(missing)
        )

    try:
        quarterly = pd.read_csv(quarterly_path)
        annual = pd.read_csv(annual_path)
        associations = build_association_results(quarterly, annual)
    except (KeyError, ValueError, pd.errors.ParserError) as exc:
        raise AssociationAnalysisError(f"association analysis failed: {exc}") from exc

    summary: dict[str, object] = {
        "association_count": int(len(associations)),
        "calculated_associations": int(
            associations["calculation_status"].eq("CALCULATED").sum()
        ),
        "quarterly_associations": int(associations["frequency"].eq("QUARTERLY").sum()),
        "annual_associations": int(associations["frequency"].eq("ANNUAL").sum()),
        "method": "SPEARMAN_RANK_CORRELATION",
        "workforce_scope": "COUNTRY_TOTAL",
        "output": str(output_dir / "association_results.csv"),
    }
    atomic_write_csv(output_dir / "association_results.csv", associations)
    atomic_write_bytes(
        output_dir / "association_summary.json",
        (json.dumps(summary, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return AssociationAnalysisResult(associations=associations, summary=summary)
