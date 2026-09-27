from pathlib import Path

import pytest

from asteria_retention.pipeline.association_analysis import (
    AssociationAnalysisError,
    build_association_analysis,
)

from test_association import annual_rows, quarterly_rows


def test_pipeline_writes_results_and_summary(tmp_path: Path):
    quarterly_rows().to_csv(tmp_path / "combined_quarterly_context.csv", index=False)
    annual_rows().to_csv(
        tmp_path / "combined_annual_inflation_context.csv", index=False
    )

    result = build_association_analysis(tmp_path)

    assert result.summary["association_count"] == 9
    assert result.summary["calculated_associations"] == 9
    assert (tmp_path / "association_results.csv").is_file()
    assert (tmp_path / "association_summary.json").is_file()


def test_pipeline_reports_missing_combined_inputs(tmp_path: Path):
    with pytest.raises(AssociationAnalysisError, match="files are missing"):
        build_association_analysis(tmp_path)
