from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_shows_recovery_message_when_database_is_missing(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("ASTERIA_DATABASE_PATH", str(tmp_path / "missing.duckdb"))

    dashboard = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    app = AppTest.from_file(dashboard).run(timeout=20)

    assert not app.exception
    assert app.error
    assert "cannot load its prepared data" in app.error[0].value
