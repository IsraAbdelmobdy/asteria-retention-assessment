import json
from pathlib import Path

from asteria_retention.pipeline.new_hire_retention import (
    prepare_new_hire_six_month_retention,
)


def test_supplied_new_hire_pipeline_reconciles_outputs(tmp_path):
    result = prepare_new_hire_six_month_retention(
        Path("data/input"), tmp_path / "canonical", tmp_path / "output"
    )

    summary = result.summary
    assert summary["cohort_hires"] == (
        summary["eligible_hires"] + summary["not_yet_measurable_hires"]
    )
    assert summary["eligible_hires"] == (
        summary["retained_hires"] + summary["exited_before_anniversary"]
    )
    assert summary["termination_on_anniversary_counts_as_retained"] is True

    persisted = json.loads(
        (tmp_path / "output" / "new_hire_6m_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert persisted == summary
    assert (tmp_path / "output" / "new_hire_6m_retention.csv").is_file()

