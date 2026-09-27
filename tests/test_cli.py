from asteria_retention.cli import main
from asteria_retention.pipeline.core import CorePipelineError, CorePipelineResult


def test_validate_config_succeeds_for_repository_root(capsys):
    result = main(["validate-config", "--project-root", "."])

    assert result == 0
    assert "6 countries, 3 indicators" in capsys.readouterr().out


def test_validate_config_reports_missing_configuration(tmp_path, capsys):
    result = main(["validate-config", "--project-root", str(tmp_path)])

    assert result == 2
    assert "Configuration is invalid" in capsys.readouterr().out


def test_run_command_reports_success(monkeypatch, tmp_path, capsys):
    def succeed(**kwargs):
        assert kwargs["offline"] is True
        return CorePipelineResult(
            mode="OFFLINE",
            completed_stages=("one", "build_database"),
            database_path=tmp_path / "asteria.duckdb",
            summary_path=tmp_path / "summary.json",
        )

    monkeypatch.setattr("asteria_retention.cli.run_core_pipeline", succeed)

    result = main(["run", "--offline"])

    assert result == 0
    assert "2 stages completed" in capsys.readouterr().out


def test_run_command_reports_named_failure(monkeypatch, capsys):
    def fail(**kwargs):
        raise CorePipelineError("stage 'ingest_inflation' failed: unavailable")

    monkeypatch.setattr("asteria_retention.cli.run_core_pipeline", fail)

    result = main(["run"])

    assert result == 2
    assert "ingest_inflation" in capsys.readouterr().out
