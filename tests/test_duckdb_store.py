from pathlib import Path

import duckdb
import pytest

from asteria_retention.storage.duckdb_store import (
    DatabaseBuildError,
    build_database,
)


CANONICAL_FILES = (
    "analytical_workforce.csv",
    "unemployment_monthly.csv",
    "job_vacancy_quarterly.csv",
    "consumer_price_inflation_annual.csv",
)

OUTPUT_FILES = (
    "new_hire_6m_retention.csv",
    "senior_hire_12m_retention.csv",
    "regretted_turnover_12m.csv",
    "unemployment_quarterly.csv",
    "combined_quarterly_context.csv",
    "combined_annual_inflation_context.csv",
    "association_results.csv",
    "workforce_quality_issues.csv",
    "workforce_excluded_records.csv",
)


def write_prepared_files(root: Path) -> tuple[Path, Path]:
    canonical = root / "canonical"
    output = root / "output"
    canonical.mkdir(parents=True)
    output.mkdir(parents=True)
    for index, name in enumerate(CANONICAL_FILES, start=1):
        (canonical / name).write_text(
            f"row_id,label\n{index},first\n{index + 10},second\n",
            encoding="utf-8",
        )
    for index, name in enumerate(OUTPUT_FILES, start=20):
        (output / name).write_text(
            f"row_id,label\n{index},only\n",
            encoding="utf-8",
        )
    return canonical, output


def test_build_creates_expected_schemas_tables_and_row_counts(tmp_path):
    canonical, output = write_prepared_files(tmp_path)
    database = output / "asteria.duckdb"

    result = build_database(canonical, output, database)

    assert database.is_file()
    assert len(result.loads) == 13
    with duckdb.connect(str(database), read_only=True) as connection:
        tables = set(
            connection.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_schema IN ('canonical', 'analytics', 'audit')"
            ).fetchall()
        )
        assert ("canonical", "workforce") in tables
        assert ("analytics", "regretted_turnover") in tables
        assert ("analytics", "combined_quarterly_context") in tables
        assert ("analytics", "association_results") in tables
        assert ("audit", "workforce_quality_issues") in tables
        assert ("audit", "table_loads") in tables
        assert connection.execute(
            "SELECT COUNT(*) FROM canonical.workforce"
        ).fetchone()[0] == 2
        assert connection.execute(
            "SELECT COUNT(*) FROM audit.table_loads"
        ).fetchone()[0] == 13


def test_missing_input_fails_before_database_is_created(tmp_path):
    canonical, output = write_prepared_files(tmp_path)
    (output / "regretted_turnover_12m.csv").unlink()
    database = output / "asteria.duckdb"

    with pytest.raises(DatabaseBuildError, match="required prepared files are missing"):
        build_database(canonical, output, database)

    assert not database.exists()


def test_failed_rebuild_preserves_existing_database(tmp_path):
    canonical, output = write_prepared_files(tmp_path)
    database = output / "asteria.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.execute("CREATE TABLE existing_marker(value INTEGER)")
        connection.execute("INSERT INTO existing_marker VALUES (42)")
    (canonical / "unemployment_monthly.csv").unlink()

    with pytest.raises(DatabaseBuildError):
        build_database(canonical, output, database)

    with duckdb.connect(str(database), read_only=True) as connection:
        assert connection.execute(
            "SELECT value FROM existing_marker"
        ).fetchone()[0] == 42
