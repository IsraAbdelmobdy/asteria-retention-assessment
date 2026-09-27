import json
from pathlib import Path

from asteria_retention.pipeline.workforce_quality import prepare_workforce


def test_supplied_workforce_quality_pipeline_matches_profile(tmp_path):
    canonical_dir = tmp_path / "canonical"
    output_dir = tmp_path / "output"

    result = prepare_workforce(Path("data/input"), canonical_dir, output_dir)

    assert result.summary["input_rows"] == 2407
    assert result.summary["exact_duplicate_rows_removed"] == 7
    assert result.summary["rows_after_deduplication"] == 2400
    assert result.summary["analytical_rows"] == 2381
    assert result.summary["excluded_rows"] == 19
    assert result.summary["metric_ineligible_rows"] == 14
    assert result.summary["hard_quarantined_rows"] == 5
    assert result.summary["issue_counts"]["COUNTRY_ALIAS_EL_GR"] == 4
    assert result.summary["issue_counts"]["COUNTRY_ALIAS_ROM_RO"] == 4
    assert result.summary["issue_counts"]["CAREER_LEVEL_ALIAS"] == 10

    persisted_summary = json.loads(
        (output_dir / "workforce_quality_summary.json").read_text(encoding="utf-8")
    )
    assert persisted_summary == result.summary
    assert (canonical_dir / "analytical_workforce.csv").is_file()
    assert (output_dir / "workforce_quality_issues.csv").is_file()
    assert (output_dir / "workforce_excluded_records.csv").is_file()
    assert (output_dir / "input_integrity_report.json").is_file()
