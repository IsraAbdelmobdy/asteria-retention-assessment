"""End-to-end supplied-workforce quality preparation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from asteria_retention.adapters.workforce_csv import SuppliedData, load_supplied_data
from asteria_retention.domain.quality import WorkforceQualityResult, assess_workforce_quality


def prepare_workforce(
    input_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    *,
    supplied: SuppliedData | None = None,
) -> WorkforceQualityResult:
    supplied = supplied or load_supplied_data(input_dir)
    result = assess_workforce_quality(supplied.events)

    canonical_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    integrity_report = {
        "package": supplied.manifest.get("package"),
        "version": supplied.manifest.get("version"),
        "workforce_as_of_date": supplied.manifest.get("workforce_as_of_date"),
        "artifacts": [check.as_dict() for check in supplied.artifact_checks],
    }

    with tempfile.TemporaryDirectory(prefix="asteria-quality-", dir=output_dir.parent) as temp:
        temp_dir = Path(temp)
        staged = {
            canonical_dir / "analytical_workforce.csv": temp_dir / "analytical_workforce.csv",
            output_dir / "workforce_excluded_records.csv": temp_dir / "workforce_excluded_records.csv",
            output_dir / "workforce_quality_issues.csv": temp_dir / "workforce_quality_issues.csv",
            output_dir / "workforce_quality_summary.json": temp_dir / "workforce_quality_summary.json",
            output_dir / "input_integrity_report.json": temp_dir / "input_integrity_report.json",
        }

        result.analytical.to_csv(
            staged[canonical_dir / "analytical_workforce.csv"], index=False
        )
        result.excluded.to_csv(
            staged[output_dir / "workforce_excluded_records.csv"], index=False
        )
        result.issues.to_csv(
            staged[output_dir / "workforce_quality_issues.csv"], index=False
        )
        staged[output_dir / "workforce_quality_summary.json"].write_text(
            json.dumps(result.summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staged[output_dir / "input_integrity_report.json"].write_text(
            json.dumps(integrity_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        for destination, source in staged.items():
            source.replace(destination)

    return result
