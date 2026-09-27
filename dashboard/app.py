"""Local interactive experience for the Asteria retention assessment."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from asteria_retention.dashboard_data import (
    DashboardData,
    DashboardDataError,
    business_unit_summary,
    filter_workforce,
    load_dashboard_data,
    metric_summary,
    relationship_summary,
    trend_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "output" / "asteria.duckdb"
OBJECTIVES = {
    "Six-month new-hire retention": "NEW_HIRE_6M",
    "Twelve-month senior-hire retention": "SENIOR_HIRE_12M",
    "Trailing-twelve-month regretted turnover": "REGRETTED_TURNOVER_12M",
}
INDICATORS = {
    "Unemployment rate": "UNEMPLOYMENT_RATE",
    "Job-vacancy rate": "JOB_VACANCY_RATE",
    "Consumer-price inflation": "CONSUMER_PRICE_INFLATION",
}


@st.cache_data(show_spinner="Loading the prepared analytical database...")
def cached_data(database_path: str, modified_ns: int) -> DashboardData:
    del modified_ns
    return load_dashboard_data(Path(database_path))


def percent(value: float | None) -> str:
    return "Not measurable" if value is None else f"{value:.1%}"


def load_data_or_stop() -> DashboardData:
    database = Path(os.environ.get("ASTERIA_DATABASE_PATH", DEFAULT_DATABASE))
    try:
        modified_ns = database.stat().st_mtime_ns if database.exists() else 0
        return cached_data(str(database), modified_ns)
    except DashboardDataError as exc:
        st.error(f"The dashboard cannot load its prepared data. {exc}")
        st.info("Run the core pipeline and rebuild the database, then refresh this page.")
        st.code("python -m asteria_retention run", language="powershell")
        st.stop()


def show_approved_findings() -> None:
    with st.expander("Four candidate-approved findings", expanded=False):
        st.markdown(
            """
1. **New-hire retention generally met its objective:** 87.2% versus 86%,
   with exceptions including 2023 and Sales.
2. **Senior-hire retention is the clearest concern:** 78.6% versus 90%,
   with strong small-cohort caution.
3. **Regretted turnover remained within the annual target:** it rose to 5.0%
   in 2025 but stayed below the 7.5% maximum.
4. **The indicators do not provide a clear overall explanation:** most
   association scores are close to zero and none establishes causation.
            """
        )


def workforce_tab(
    data: DashboardData,
    objective_id: str,
    country: str,
    business_unit: str,
    year_range: tuple[int, int],
) -> None:
    selected = filter_workforce(
        data.quarterly,
        objective_id=objective_id,
        country_code=country,
        business_unit=business_unit,
        start_year=year_range[0],
        end_year=year_range[1],
    )
    summary = metric_summary(selected, objective_id)
    if summary is None:
        st.warning("No measurable workforce result matches the current filters.")
        return

    rate, target, status = st.columns(3)
    rate.metric("Calculated rate", percent(summary["rate"]))
    target.metric("Objective", percent(summary["target"]))
    status.metric("Objective status", str(summary["target_status"]))
    st.caption(f"{summary['scope_note']}. Numerator {summary['numerator']:,.0f}; denominator {summary['denominator']:,.1f}.")
    if summary["warned_rows"]:
        st.warning(
            f"{summary['warned_rows']} selected rows carry a small-sample or "
            "low-headcount warning. The rates remain visible but require caution."
        )

    trend = trend_summary(selected).set_index("period")
    st.subheader("Trend and objective")
    st.line_chart(
        trend[["workforce_rate", "target_value"]],
        y_label="Rate",
        color=["#006D77", "#B54708"],
    )
    st.caption(
        "The objective line is shown separately so status is not communicated by colour alone."
    )

    st.subheader("Business-unit comparison")
    segments = business_unit_summary(
        data.quarterly,
        objective_id=objective_id,
        country_code=country,
        start_year=year_range[0],
        end_year=year_range[1],
    )
    if segments.empty:
        st.info("No measurable business-unit results match the current filters.")
    else:
        st.bar_chart(
            segments.set_index("business_unit")["workforce_rate"],
            y_label="Rate",
            color="#006D77",
        )
        display = segments.copy()
        display["workforce_rate"] = display["workforce_rate"].map(lambda x: f"{x:.1%}")
        st.dataframe(display, hide_index=True, width="stretch")


def economic_tab(
    data: DashboardData,
    objective_id: str,
    country: str,
    year_range: tuple[int, int],
) -> None:
    st.info(
        "Relationship calculations always use country totals. The business-unit "
        "filter does not apply because each external indicator is national."
    )
    indicator_label = st.selectbox("Economic indicator", list(INDICATORS))
    indicator_id = INDICATORS[indicator_label]
    pairs, coefficient, status = relationship_summary(
        data,
        objective_id=objective_id,
        indicator_id=indicator_id,
        country_code=country,
        start_year=year_range[0],
        end_year=year_range[1],
    )
    score, sample = st.columns(2)
    score.metric(
        "Spearman score for current filters",
        "Not calculated" if coefficient is None else f"{coefficient:.3f}",
    )
    sample.metric("Usable paired observations", len(pairs))
    st.caption(f"Calculation status: {status.replace('_', ' ').title()}.")
    if pairs.empty:
        st.warning("No complete workforce/economic pairs match the current filters.")
        return
    st.scatter_chart(
        pairs,
        x="indicator_value",
        y="workforce_rate",
        color="country_code",
        x_label=indicator_label,
        y_label="Workforce rate",
    )
    warned = int(pairs["sample_warning"].fillna("").ne("").sum())
    if warned:
        st.warning(f"{warned} of these workforce observations carry a sample warning.")
    st.warning(
        "Association is not causation. Repeated country observations, other possible "
        "influences, and current-vintage revisions limit interpretation."
    )


def trust_tab(data: DashboardData) -> None:
    st.subheader("Coverage and quality")
    issue, excluded, tables = st.columns(3)
    issue.metric("Quality evidence rows", len(data.quality_issues))
    excluded.metric("Excluded source rows", len(data.excluded_records))
    tables.metric("Loaded analytical files", len(data.table_loads))

    st.subheader("External-data retrieval")
    st.dataframe(data.source_freshness, hide_index=True, width="stretch")
    st.caption(
        "These are retrieval times for the current downloaded versions. They are not "
        "the dates on which each historical value first became publicly available."
    )

    st.subheader("Sources and attribution")
    st.markdown(
        """
- [Eurostat unemployment](https://ec.europa.eu/eurostat/databrowser/view/une_rt_m/default/table)
- [Eurostat job vacancies](https://ec.europa.eu/eurostat/databrowser/view/jvs_q_nace2/default/table)
- [World Bank consumer-price inflation](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG) — CC BY 4.0
        """
    )
    st.subheader("Method in plain language")
    st.markdown(
        """
- Hire retention is grouped by hire quarter and checks the approved calendar-month anniversary.
- Turnover uses regretted exits divided by the average of twelve month-end headcounts.
- Hire cohorts use economic context from the hire quarter; turnover uses matching trailing context.
- Inflation remains annual and is never copied into artificial quarterly observations.
- Spearman correlation compares the ordering of two measures from low to high.
- Missing classifications remain unknown; invalid rows have visible reason codes.
        """
    )
    with st.expander("Known limitations"):
        st.markdown(
            """
- Business unit is assumed constant because transfer history was not supplied.
- Senior-hire groups are small.
- Countries repeat over time and are not independent experiments.
- National indicators may not describe each employee's local conditions.
- External values may have been revised after the workforce period.
- Early 2021 trailing context includes the exceptional 2020 COVID-19 period.
            """
        )


st.set_page_config(
    page_title="Asteria retention evidence",
    page_icon="📊",
    layout="wide",
)
st.title("Asteria retention evidence")
st.caption("Auditable workforce objectives with aligned public economic context")

dashboard_data = load_data_or_stop()
show_approved_findings()

with st.sidebar:
    st.header("Explore")
    objective_label = st.selectbox("Retention objective", list(OBJECTIVES))
    objective = OBJECTIVES[objective_label]
    countries = ["ALL"] + sorted(dashboard_data.quarterly["country_code"].dropna().unique())
    country_filter = st.selectbox(
        "Country", countries, format_func=lambda value: "All countries" if value == "ALL" else value
    )
    units = ["ALL"] + sorted(
        dashboard_data.quarterly.loc[
            dashboard_data.quarterly["aggregation_level"].eq("BUSINESS_UNIT"),
            "business_unit",
        ].dropna().unique()
    )
    unit_filter = st.selectbox(
        "Business unit", units, format_func=lambda value: "All business units" if value == "ALL" else value
    )
    available_years = dashboard_data.quarterly["period"].str[:4].astype(int)
    selected_years = st.slider(
        "Years",
        int(available_years.min()),
        int(available_years.max()),
        (int(available_years.min()), int(available_years.max())),
    )

workforce, economic, trust = st.tabs(
    ["Workforce results", "Economic context", "Trust and methodology"]
)
with workforce:
    workforce_tab(
        dashboard_data,
        objective,
        country_filter,
        unit_filter,
        selected_years,
    )
with economic:
    economic_tab(dashboard_data, objective, country_filter, selected_years)
with trust:
    trust_tab(dashboard_data)
