import json
from pathlib import Path

from asteria_retention.pipeline.senior_hire_retention import (
    prepare_senior_hire_twelve_month_retention,
)


def test_supplied_senior_hire_pipeline_reconciles_outputs(tmp_path):
    result = prepare_senior_hire_twelve_month_retention(
        Path("data/input"), tmp_path / "canonical", tmp_path / "output"
    )

    summary = result.summary
    assert summary["cohort_hires"] == (
        summary["eligible_hires"] + summary["not_yet_measurable_hires"]
    )
    assert summary["eligible_hires"] == (
        summary["retained_hires"] + summary["exited_before_anniversary"]
    )
    assert summary["included_career_levels"] == ["Senior Leader"]
    assert summary["manager_is_senior"] is False

    persisted = json.loads(
        (tmp_path / "output" / "senior_hire_12m_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert persisted == summary
    assert (tmp_path / "output" / "senior_hire_12m_retention.csv").is_file()
