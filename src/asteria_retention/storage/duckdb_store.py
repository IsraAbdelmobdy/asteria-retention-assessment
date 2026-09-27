"""Atomic DuckDB build from validated prepared project artifacts."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb


class DatabaseBuildError(RuntimeError):
    """Raised when the prepared artifacts cannot produce a complete database."""


@dataclass(frozen=True)
class TableLoad:
    schema_name: str
    table_name: str
    source_file: Path
    row_count: int


@dataclass(frozen=True)
class DatabaseBuildResult:
    database_path: Path
    loads: tuple[TableLoad, ...]
    built_at_utc: str


def _table_contract(
    canonical_dir: Path, output_dir: Path
) -> tuple[tuple[str, str, Path], ...]:
    return (
        ("canonical", "workforce", canonical_dir / "analytical_workforce.csv"),
        (
            "canonical",
            "unemployment_monthly",
            canonical_dir / "unemployment_monthly.csv",
        ),
        (
            "canonical",
            "job_vacancy_quarterly",
            canonical_dir / "job_vacancy_quarterly.csv",
        ),
        (
            "canonical",
            "inflation_annual",
            canonical_dir / "consumer_price_inflation_annual.csv",
        ),
        (
            "analytics",
            "new_hire_retention",
            output_dir / "new_hire_6m_retention.csv",
        ),
        (
            "analytics",
            "senior_hire_retention",
            output_dir / "senior_hire_12m_retention.csv",
        ),
        (
            "analytics",
            "regretted_turnover",
            output_dir / "regretted_turnover_12m.csv",
        ),
        (
            "analytics",
            "unemployment_quarterly",
            output_dir / "unemployment_quarterly.csv",
        ),
        (
            "analytics",
            "combined_quarterly_context",
            output_dir / "combined_quarterly_context.csv",
        ),
        (
            "analytics",
            "combined_annual_inflation_context",
            output_dir / "combined_annual_inflation_context.csv",
        ),
        (
            "analytics",
            "association_results",
            output_dir / "association_results.csv",
        ),
        (
            "audit",
            "workforce_quality_issues",
            output_dir / "workforce_quality_issues.csv",
        ),
        (
            "audit",
            "workforce_excluded_records",
            output_dir / "workforce_excluded_records.csv",
        ),
    )


def build_database(
    canonical_dir: Path,
    output_dir: Path,
    database_path: Path,
) -> DatabaseBuildResult:
    """Build all contracted tables, then atomically replace the database file."""

    contract = _table_contract(canonical_dir, output_dir)
    missing = [str(path) for _, _, path in contract if not path.is_file()]
    if missing:
        raise DatabaseBuildError(
            "required prepared files are missing: " + ", ".join(missing)
        )

    database_path.parent.mkdir(parents=True, exist_ok=True)
    built_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    loads: list[TableLoad] = []

    try:
        with tempfile.TemporaryDirectory(
            prefix="asteria-duckdb-", dir=database_path.parent
        ) as temporary_directory:
            temporary_database = Path(temporary_directory) / database_path.name
            connection = duckdb.connect(str(temporary_database))
            try:
                for schema_name in ("canonical", "analytics", "audit"):
                    connection.execute(f"CREATE SCHEMA {schema_name}")

                for schema_name, table_name, source_file in contract:
                    qualified_name = f"{schema_name}.{table_name}"
                    connection.execute(
                        f"CREATE TABLE {qualified_name} AS "
                        "SELECT * FROM read_csv_auto(?, header = true)",
                        [str(source_file.resolve())],
                    )
                    row_count = int(
                        connection.execute(
                            f"SELECT COUNT(*) FROM {qualified_name}"
                        ).fetchone()[0]
                    )
                    loads.append(
                        TableLoad(
                            schema_name=schema_name,
                            table_name=table_name,
                            source_file=source_file,
                            row_count=row_count,
                        )
                    )

                connection.execute(
                    """
                    CREATE TABLE audit.table_loads (
                        schema_name VARCHAR NOT NULL,
                        table_name VARCHAR NOT NULL,
                        source_file VARCHAR NOT NULL,
                        row_count BIGINT NOT NULL,
                        built_at_utc VARCHAR NOT NULL
                    )
                    """
                )
                connection.executemany(
                    "INSERT INTO audit.table_loads VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            load.schema_name,
                            load.table_name,
                            str(load.source_file),
                            load.row_count,
                            built_at,
                        )
                        for load in loads
                    ],
                )
                audit_count = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM audit.table_loads"
                    ).fetchone()[0]
                )
                if audit_count != len(contract):
                    raise DatabaseBuildError(
                        "audit.table_loads does not reconcile with the table contract"
                    )
                connection.execute("CHECKPOINT")
            finally:
                connection.close()

            temporary_database.replace(database_path)
    except DatabaseBuildError:
        raise
    except (duckdb.Error, OSError) as exc:
        raise DatabaseBuildError(f"DuckDB build failed: {exc}") from exc

    return DatabaseBuildResult(
        database_path=database_path,
        loads=tuple(loads),
        built_at_utc=built_at,
    )
