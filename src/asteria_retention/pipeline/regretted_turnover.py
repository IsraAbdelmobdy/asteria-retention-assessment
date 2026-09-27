"""Re-runnable pipeline for trailing-twelve-month regretted turnover."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from asteria_retention.adapters.workforce_csv import SuppliedData, load_supplied_data
from asteria_retention.domain.quality import WorkforceQualityResult
from asteria_retention.domain.retention import (
    RetentionContractError,
    RetentionMetricResult,
    calculate_regretted_turnover_twelve_month,
)
from asteria_retention.pipeline.workforce_quality import prepare_workforce


def prepare_regretted_turnover_twelve_month(
    input_dir: Path,
    canonical_dir: Path,
    output_dir: Path,
    *,
    quality_result: WorkforceQualityResult | None = None,
    supplied: SuppliedData | None = None,
) -> RetentionMetricResult:
    supplied = supplied or load_supplied_data(input_dir)
    quality_result = quality_result or prepare_workforce(
        input_dir, canonical_dir, output_dir, supplied=supplied
    )

    objective_rows = supplied.objectives.loc[
        supplied.objectives["objective_id"].eq("REGRETTED_TURNOVER_12M")
    ]
    if len(objective_rows) != 1:
        raise RetentionContractError(
            "retention_objectives.csv must contain exactly one REGRETTED_TURNOVER_12M row"
        )

    result = calculate_regretted_turnover_twelve_month(
        quality_result.analytical,
        objective_rows.iloc[0].to_dict(),
        as_of_date=str(supplied.manifest["workforce_as_of_date"]),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="asteria-retention-", dir=output_dir.parent) as temp:
        temp_dir = Path(temp)
        metrics_source = temp_dir / "regretted_turnover_12m.csv"
        summary_source = temp_dir / "regretted_turnover_12m_summary.json"
        result.metrics.to_csv(metrics_source, index=False)
        summary_source.write_text(
            json.dumps(result.summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        metrics_source.replace(output_dir / metrics_source.name)
        summary_source.replace(output_dir / summary_source.name)

    return result
