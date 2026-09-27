"""Read-only dashboard data access and presentation-safe summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from asteria_retention.domain.association import calculate_spearman


class DashboardDataError(RuntimeError):
    """Raised when the prepared dashboard database cannot be read safely."""


@dataclass(frozen=True)
class DashboardData:
    quarterly: pd.DataFrame
    annual: pd.DataFrame
    associations: pd.DataFrame
    quality_issues: pd.DataFrame
    excluded_records: pd.DataFrame
    table_loads: pd.DataFrame
    source_freshness: pd.DataFrame


REQUIRED_TABLES = {
    ("analytics", "combined_quarterly_context"),
    ("analytics", "combined_annual_inflation_context"),
    ("analytics", "association_results"),
    ("audit", "workforce_quality_issues"),
    ("audit", "workforce_excluded_records"),
    ("audit", "table_loads"),
    ("canonical", "unemployment_monthly"),
    ("canonical", "job_vacancy_quarterly"),
    ("canonical", "inflation_annual"),
}


def load_dashboard_data(database_path: Path) -> DashboardData:
    if not database_path.is_file():
        raise DashboardDataError(f"database not found: {database_path}")
    try:
        with duckdb.connect(str(database_path), read_only=True) as connection:
            available = set(
                connection.execute(
                    "SELECT table_schema, table_name FROM information_schema.tables"
                ).fetchall()
            )
            missing = sorted(REQUIRED_TABLES.difference(available))
            if missing:
                names = ", ".join(f"{schema}.{table}" for schema, table in missing)
                raise DashboardDataError("database is missing required tables: " + names)

            freshness = connection.execute(
                """
                SELECT 'Eurostat unemployment' AS source,
                       MAX(retrieved_at_utc) AS retrieved_at_utc
                FROM canonical.unemployment_monthly
                UNION ALL
                SELECT 'Eurostat job vacancies', MAX(retrieved_at_utc)
                FROM canonical.job_vacancy_quarterly
                UNION ALL
                SELECT 'World Bank inflation', MAX(retrieved_at_utc)
                FROM canonical.inflation_annual
                """
            ).fetchdf()
            return DashboardData(
                quarterly=connection.execute(
                    "SELECT * FROM analytics.combined_quarterly_context"
                ).fetchdf(),
                annual=connection.execute(
                    "SELECT * FROM analytics.combined_annual_inflation_context"
                ).fetchdf(),
                associations=connection.execute(
                    "SELECT * FROM analytics.association_results"
                ).fetchdf(),
                quality_issues=connection.execute(
                    "SELECT * FROM audit.workforce_quality_issues"
                ).fetchdf(),
                excluded_records=connection.execute(
                    "SELECT * FROM audit.workforce_excluded_records"
                ).fetchdf(),
                table_loads=connection.execute(
                    "SELECT * FROM audit.table_loads"
                ).fetchdf(),
                source_freshness=freshness,
            )
    except DashboardDataError:
        raise
    except (duckdb.Error, OSError) as exc:
        raise DashboardDataError(f"could not read dashboard database: {exc}") from exc


def filter_workforce(
    quarterly: pd.DataFrame,
    *,
    objective_id: str,
    country_code: str,
    business_unit: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    frame = quarterly.loc[quarterly["objective_id"].eq(objective_id)].copy()
    years = frame["period"].str[:4].astype(int)
    frame = frame.loc[years.between(start_year, end_year)]
    if country_code != "ALL":
        frame = frame.loc[frame["country_code"].eq(country_code)]
    if business_unit == "ALL":
        frame = frame.loc[frame["aggregation_level"].eq("COUNTRY_TOTAL")]
    else:
        frame = frame.loc[
            frame["aggregation_level"].eq("BUSINESS_UNIT")
            & frame["business_unit"].eq(business_unit)
        ]
    return frame.reset_index(drop=True)


def metric_summary(frame: pd.DataFrame, objective_id: str) -> dict[str, object] | None:
    measurable = frame.loc[frame["denominator"].fillna(0).gt(0)].copy()
    if measurable.empty:
        return None
    if objective_id == "REGRETTED_TURNOVER_12M":
        period = str(measurable["period"].max())
        included = measurable.loc[measurable["period"].eq(period)]
        scope_note = f"Latest selected trailing window: {period}"
    else:
        included = measurable
        period = f"{measurable['period'].min()} to {measurable['period'].max()}"
        scope_note = "All measurable selected hire cohorts"
    numerator = float(included["numerator"].sum())
    denominator = float(included["denominator"].sum())
    rate = numerator / denominator if denominator > 0 else None
    target = float(included["target_value"].iloc[0])
    target_met = (
        rate <= target
        if objective_id == "REGRETTED_TURNOVER_12M"
        else rate >= target
    )
    return {
        "rate": rate,
        "target": target,
        "target_status": "MET" if target_met else "MISSED",
        "numerator": numerator,
        "denominator": denominator,
        "period": period,
        "scope_note": scope_note,
        "warned_rows": int(measurable["sample_warning"].fillna("").ne("").sum()),
    }


def trend_summary(frame: pd.DataFrame) -> pd.DataFrame:
    measurable = frame.loc[frame["denominator"].fillna(0).gt(0)]
    if measurable.empty:
        return pd.DataFrame(columns=["period", "workforce_rate", "target_value"])
    grouped = (
        measurable.groupby("period", sort=True)
        .agg(
            numerator=("numerator", "sum"),
            denominator=("denominator", "sum"),
            target_value=("target_value", "first"),
        )
        .reset_index()
    )
    grouped["workforce_rate"] = grouped["numerator"] / grouped["denominator"]
    return grouped[["period", "workforce_rate", "target_value"]]


def business_unit_summary(
    quarterly: pd.DataFrame,
    *,
    objective_id: str,
    country_code: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    all_units = quarterly.loc[
        quarterly["objective_id"].eq(objective_id)
        & quarterly["aggregation_level"].eq("BUSINESS_UNIT")
    ].copy()
    years = all_units["period"].str[:4].astype(int)
    all_units = all_units.loc[years.between(start_year, end_year)]
    if country_code != "ALL":
        all_units = all_units.loc[all_units["country_code"].eq(country_code)]
    all_units = all_units.loc[all_units["denominator"].fillna(0).gt(0)]
    if all_units.empty:
        return pd.DataFrame(columns=["business_unit", "workforce_rate"])
    if objective_id == "REGRETTED_TURNOVER_12M":
        all_units = all_units.loc[all_units["period"].eq(all_units["period"].max())]
    grouped = (
        all_units.groupby("business_unit", sort=True)
        .agg(numerator=("numerator", "sum"), denominator=("denominator", "sum"))
        .reset_index()
    )
    grouped["workforce_rate"] = grouped["numerator"] / grouped["denominator"]
    return grouped[["business_unit", "workforce_rate"]]


def relationship_summary(
    data: DashboardData,
    *,
    objective_id: str,
    indicator_id: str,
    country_code: str,
    start_year: int,
    end_year: int,
) -> tuple[pd.DataFrame, float | None, str]:
    if indicator_id == "CONSUMER_PRICE_INFLATION":
        frame = data.annual.loc[
            data.annual["objective_id"].eq(objective_id)
            & data.annual["aggregation_level"].eq("COUNTRY_TOTAL")
        ].copy()
        frame = frame.loc[frame["reference_year"].between(start_year, end_year)]
        indicator_column = "inflation_rate"
        period_column = "reference_year"
    else:
        frame = data.quarterly.loc[
            data.quarterly["objective_id"].eq(objective_id)
            & data.quarterly["aggregation_level"].eq("COUNTRY_TOTAL")
        ].copy()
        years = frame["period"].str[:4].astype(int)
        frame = frame.loc[years.between(start_year, end_year)]
        indicator_column = (
            "unemployment_rate"
            if indicator_id == "UNEMPLOYMENT_RATE"
            else "job_vacancy_rate"
        )
        period_column = "period"
    if country_code != "ALL":
        frame = frame.loc[frame["country_code"].eq(country_code)]
    pairs = frame.loc[
        frame["workforce_rate"].notna() & frame[indicator_column].notna(),
        [
            "country_code",
            period_column,
            "workforce_rate",
            indicator_column,
            "sample_warning",
        ],
    ].copy()
    pairs = pairs.rename(columns={period_column: "period", indicator_column: "indicator_value"})
    coefficient, status = calculate_spearman(
        pairs, "workforce_rate", "indicator_value"
    )
    return pairs.reset_index(drop=True), coefficient, status
