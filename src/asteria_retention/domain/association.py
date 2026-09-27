"""Simple, auditable associations between workforce outcomes and context."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AssociationSpec:
    objective_id: str
    indicator_id: str
    indicator_column: str
    frequency: str


SPECS = (
    AssociationSpec("NEW_HIRE_6M", "UNEMPLOYMENT_RATE", "unemployment_rate", "QUARTERLY"),
    AssociationSpec("NEW_HIRE_6M", "JOB_VACANCY_RATE", "job_vacancy_rate", "QUARTERLY"),
    AssociationSpec("SENIOR_HIRE_12M", "UNEMPLOYMENT_RATE", "unemployment_rate", "QUARTERLY"),
    AssociationSpec("SENIOR_HIRE_12M", "JOB_VACANCY_RATE", "job_vacancy_rate", "QUARTERLY"),
    AssociationSpec("REGRETTED_TURNOVER_12M", "UNEMPLOYMENT_RATE", "unemployment_rate", "QUARTERLY"),
    AssociationSpec("REGRETTED_TURNOVER_12M", "JOB_VACANCY_RATE", "job_vacancy_rate", "QUARTERLY"),
    AssociationSpec("NEW_HIRE_6M", "CONSUMER_PRICE_INFLATION", "inflation_rate", "ANNUAL"),
    AssociationSpec("SENIOR_HIRE_12M", "CONSUMER_PRICE_INFLATION", "inflation_rate", "ANNUAL"),
    AssociationSpec("REGRETTED_TURNOVER_12M", "CONSUMER_PRICE_INFLATION", "inflation_rate", "ANNUAL"),
)


def _direction(coefficient: float | None) -> str:
    if coefficient is None:
        return "NOT_CALCULATED"
    if coefficient > 0:
        return "POSITIVE"
    if coefficient < 0:
        return "NEGATIVE"
    return "ZERO"


def calculate_spearman(
    pairs: pd.DataFrame,
    workforce_column: str,
    indicator_column: str,
) -> tuple[float | None, str]:
    """Calculate one rank correlation with explicit non-calculation reasons."""
    if len(pairs) < 2:
        return None, "INSUFFICIENT_PAIRED_OBSERVATIONS"
    if pairs[workforce_column].nunique() < 2:
        return None, "NO_WORKFORCE_VARIATION"
    if pairs[indicator_column].nunique() < 2:
        return None, "NO_INDICATOR_VARIATION"
    coefficient = float(
        pairs[workforce_column].rank(method="average").corr(
            pairs[indicator_column].rank(method="average")
        )
    )
    return coefficient, "CALCULATED"


def _one_association(frame: pd.DataFrame, spec: AssociationSpec) -> dict[str, object]:
    period_column = "period" if spec.frequency == "QUARTERLY" else "reference_year"
    objective = frame.loc[
        frame["objective_id"].eq(spec.objective_id)
        & frame["aggregation_level"].eq("COUNTRY_TOTAL")
    ].copy()
    pairs = objective.loc[
        objective["workforce_rate"].notna() & objective[spec.indicator_column].notna()
    ].copy()

    coefficient, status = calculate_spearman(
        pairs, "workforce_rate", spec.indicator_column
    )

    warnings = pairs["sample_warning"].fillna("").ne("")
    return {
        "objective_id": spec.objective_id,
        "indicator_id": spec.indicator_id,
        "frequency": spec.frequency,
        "workforce_scope": "COUNTRY_TOTAL",
        "method": "SPEARMAN_RANK_CORRELATION",
        "paired_observations": int(len(pairs)),
        "countries": int(pairs["country_code"].nunique()),
        "period_start": str(pairs[period_column].min()) if len(pairs) else "",
        "period_end": str(pairs[period_column].max()) if len(pairs) else "",
        "coefficient": coefficient,
        "direction": _direction(coefficient),
        "calculation_status": status,
        "warned_workforce_rows": int(warnings.sum()),
        "interpretation_warning": (
            "ASSOCIATION_NOT_CAUSATION|REPEATED_COUNTRY_OBSERVATIONS|"
            "CURRENT_EXTERNAL_DATA_VINTAGE"
        ),
    }


def build_association_results(
    quarterly_context: pd.DataFrame,
    annual_context: pd.DataFrame,
) -> pd.DataFrame:
    """Return the nine approved, country-total Spearman comparisons."""
    quarterly_required = {
        "objective_id",
        "aggregation_level",
        "country_code",
        "period",
        "workforce_rate",
        "unemployment_rate",
        "job_vacancy_rate",
        "sample_warning",
    }
    annual_required = {
        "objective_id",
        "aggregation_level",
        "country_code",
        "reference_year",
        "workforce_rate",
        "inflation_rate",
        "sample_warning",
    }
    missing_quarterly = quarterly_required.difference(quarterly_context.columns)
    missing_annual = annual_required.difference(annual_context.columns)
    if missing_quarterly or missing_annual:
        missing = sorted(missing_quarterly | missing_annual)
        raise ValueError("combined context is missing columns: " + ", ".join(missing))

    records = []
    for spec in SPECS:
        source = quarterly_context if spec.frequency == "QUARTERLY" else annual_context
        records.append(_one_association(source, spec))
    return pd.DataFrame(records)
