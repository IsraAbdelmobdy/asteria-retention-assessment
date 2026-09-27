import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import asteria_retention.pipeline.core as core
from asteria_retention.pipeline.core import CorePipelineError, run_core_pipeline
from asteria_retention.pipeline.core import prepare_offline_external_data


def paths(tmp_path: Path) -> dict[str, object]:
    return {
        "project_root": tmp_path,
        "input_dir": tmp_path / "input",
        "raw_dir": tmp_path / "raw",
        "canonical_dir": tmp_path / "canonical",
        "output_dir": tmp_path / "output",
        "database_path": tmp_path / "output" / "asteria.duckdb",
    }


def install_stage_spies(monkeypatch, calls: list[str]) -> None:
    def stage(name, result=None):
        def execute(*args, **kwargs):
            calls.append(name)
            return result if result is not None else SimpleNamespace()

        return execute

    monkeypatch.setattr(core, "load_project_config", stage("config", {}))
    monkeypatch.setattr(core, "load_supplied_data", stage("supplied"))
    monkeypatch.setattr(core, "prepare_workforce", stage("workforce"))
    monkeypatch.setattr(core, "prepare_new_hire_six_month_retention", stage("new"))
    monkeypatch.setattr(
        core, "prepare_senior_hire_twelve_month_retention", stage("senior")
    )
    monkeypatch.setattr(
        core, "prepare_regretted_turnover_twelve_month", stage("turnover")
    )
    monkeypatch.setattr(core, "ingest_unemployment", stage("unemployment"))
    monkeypatch.setattr(core, "ingest_job_vacancy", stage("vacancy"))
    monkeypatch.setattr(core, "ingest_inflation", stage("inflation"))
    monkeypatch.setattr(
        core,
        "prepare_offline_external_data",
        stage("offline", "CACHED_CANONICAL"),
    )
    monkeypatch.setattr(core, "build_combined_context", stage("combined"))
    monkeypatch.setattr(core, "build_association_analysis", stage("associations"))
    monkeypatch.setattr(core, "build_database", stage("database"))


def test_online_run_executes_database_last_and_writes_success_summary(
    tmp_path, monkeypatch
):
    calls: list[str] = []
    install_stage_spies(monkeypatch, calls)

    result = run_core_pipeline(**paths(tmp_path), offline=False)

    assert calls == [
        "config",
        "supplied",
        "workforce",
        "new",
        "senior",
        "turnover",
        "unemployment",
        "vacancy",
        "inflation",
        "combined",
        "associations",
        "database",
    ]
    assert result.completed_stages[-1] == "build_database"
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "SUCCEEDED"
    assert summary["mode"] == "ONLINE"


def test_offline_run_validates_cache_and_never_calls_download_stages(
    tmp_path, monkeypatch
):
    calls: list[str] = []
    install_stage_spies(monkeypatch, calls)

    result = run_core_pipeline(**paths(tmp_path), offline=True)

    assert "offline" in calls
    assert "unemployment" not in calls
    assert "vacancy" not in calls
    assert "inflation" not in calls
    assert result.mode == "OFFLINE"


def test_failed_stage_is_named_and_database_stage_is_not_called(
    tmp_path, monkeypatch
):
    calls: list[str] = []
    install_stage_spies(monkeypatch, calls)

    def fail(*args, **kwargs):
        calls.append("vacancy")
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(core, "ingest_job_vacancy", fail)

    with pytest.raises(CorePipelineError, match="ingest_job_vacancy"):
        run_core_pipeline(**paths(tmp_path), offline=False)

    assert "database" not in calls
    summary = json.loads(
        (tmp_path / "output" / "core_run_summary.json").read_text(encoding="utf-8")
    )
    assert summary["status"] == "FAILED"
    assert summary["failed_stage"] == "ingest_job_vacancy"


def test_offline_falls_back_to_checked_replay_fixtures(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    source = prepare_offline_external_data(
        project_root,
        tmp_path / "raw",
        tmp_path / "canonical",
        tmp_path / "output",
    )

    assert source == "REPLAY_FIXTURES"
    assert len(pd.read_csv(tmp_path / "canonical" / "unemployment_monthly.csv")) == 432
    assert len(pd.read_csv(tmp_path / "canonical" / "job_vacancy_quarterly.csv")) == 144
    assert len(
        pd.read_csv(tmp_path / "canonical" / "consumer_price_inflation_annual.csv")
    ) == 30


def test_complete_offline_workflow_can_start_without_generated_external_files(
    tmp_path,
):
    project_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "output"

    result = run_core_pipeline(
        project_root=project_root,
        input_dir=project_root / "data" / "input",
        raw_dir=tmp_path / "raw",
        canonical_dir=tmp_path / "canonical",
        output_dir=output,
        database_path=output / "asteria.duckdb",
        offline=True,
    )

    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "SUCCEEDED"
    assert summary["offline_external_source"] == "REPLAY_FIXTURES"
    assert result.database_path.is_file()
