import json
from pathlib import Path

from asteria_retention.pipeline.regretted_turnover import (
    prepare_regretted_turnover_twelve_month,
)


def test_supplied_regretted_turnover_pipeline_reconciles_outputs(tmp_path):
    result = prepare_regretted_turnover_twelve_month(
        Path("data/input"), tmp_path / "canonical", tmp_path / "output"
    )

    assert result.summary["reporting_quarters"] == 20
    assert result.summary["country_quarter_rows"] == 120
    assert result.summary["month_end_observations_per_window"] == 12
    assert result.summary["unknown_regretted_classification_is_not_imputed"] is True
    assert result.summary["business_unit_is_treated_as_constant"] is True

    persisted = json.loads(
        (tmp_path / "output" / "regretted_turnover_12m_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert persisted == result.summary
    assert (tmp_path / "output" / "regretted_turnover_12m.csv").is_file()
