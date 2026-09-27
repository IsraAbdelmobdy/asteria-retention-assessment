"""Temporal alignment of workforce outcomes and external context."""

from __future__ import annotations

import pandas as pd


RETROSPECTIVE_WARNING = (
    "RETROSPECTIVE_CURRENT_VINTAGE: external values may have been published or "
    "revised after the workforce period."
)


def _quarter_boundaries(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    periods = pd.PeriodIndex(values.str.replace("-Q", "Q", regex=False), freq="Q")
    return (
        pd.Series(periods.start_time.strftime("%Y-%m-%d"), index=values.index),
        pd.Series(periods.end_time.strftime("%Y-%m-%d"), index=values.index),
    )


def _direct_quarterly_external_context(
    unemployment_quarterly: pd.DataFrame,
    job_vacancy_quarterly: pd.DataFrame,
) -> pd.DataFrame:
    unemployment = unemployment_quarterly.rename(
        columns={
            "reporting_quarter": "period",
            "monthly_observations": "unemployment_observations",
            "coverage_status": "unemployment_coverage_status",
        }
    )[
        [
            "country_code",
            "period",
            "unemployment_rate",
            "unemployment_observations",
            "unemployment_coverage_status",
        ]
    ]
    vacancy = job_vacancy_quarterly.rename(
        columns={
            "reference_period": "period",
            "value": "job_vacancy_rate",
            "observation_status": "job_vacancy_statuses",
            "is_provisional": "job_vacancy_has_provisional",
            "coverage_note_code": "job_vacancy_coverage_note_code",
        }
    )[
        [
            "country_code",
            "period",
            "job_vacancy_rate",
            "job_vacancy_statuses",
            "job_vacancy_has_provisional",
            "job_vacancy_coverage_note_code",
        ]
    ]
    vacancy["job_vacancy_observations"] = vacancy["job_vacancy_rate"].notna().astype(int)
    vacancy["job_vacancy_coverage_status"] = vacancy[
        "job_vacancy_rate"
    ].notna().map({True: "COMPLETE", False: "INCOMPLETE"})
    return unemployment.merge(
        vacancy,
        on=["country_code", "period"],
        how="outer",
        validate="one_to_one",
    )


def _cohort_quarterly_rows(
    metric: pd.DataFrame,
    *,
    workforce_metric: str,
    external_context: pd.DataFrame,
) -> pd.DataFrame:
    frame = metric.copy().rename(
        columns={
            "cohort_quarter": "period",
            "retained_hires": "numerator",
            "eligible_hires": "denominator",
            "retention_rate": "workforce_rate",
        }
    )
    if "sample_warning" not in frame.columns:
        frame["sample_warning"] = ""
        frame.loc[
            frame["denominator"].between(1, 9, inclusive="both"),
            "sample_warning",
        ] = "SMALL_SAMPLE"
    starts, ends = _quarter_boundaries(frame["period"])
    frame["period_start"] = starts
    frame["period_end"] = ends
    frame["workforce_metric"] = workforce_metric
    frame["workforce_window"] = "HIRE_COHORT_QUARTER"
    frame["external_context_window"] = "SAME_QUARTER"
    frame = frame.merge(
        external_context,
        on=["country_code", "period"],
        how="left",
        validate="many_to_one",
    )
    frame["retrospective_warning"] = RETROSPECTIVE_WARNING
    return frame


def _trailing_external_context(
    unemployment_monthly: pd.DataFrame,
    job_vacancy_quarterly: pd.DataFrame,
    country_periods: pd.DataFrame,
) -> pd.DataFrame:
    unemployment = unemployment_monthly.copy()
    unemployment["month"] = pd.PeriodIndex(
        unemployment["reference_period"], freq="M"
    )
    vacancy = job_vacancy_quarterly.copy()
    vacancy["quarter"] = pd.PeriodIndex(
        vacancy["reference_period"].str.replace("-Q", "Q", regex=False), freq="Q"
    )
    records: list[dict[str, object]] = []

    for row in country_periods.itertuples(index=False):
        end_quarter = pd.Period(str(row.period).replace("-Q", "Q"), freq="Q")
        end_month = end_quarter.asfreq("M", how="end")
        start_month = end_month - 11
        country_unemployment = unemployment.loc[
            unemployment["country_code"].eq(row.country_code)
            & unemployment["month"].between(start_month, end_month)
        ]
        unemployment_count = int(country_unemployment["value"].notna().sum())
        unemployment_rate = (
            float(country_unemployment["value"].mean())
            if unemployment_count == 12 and len(country_unemployment) == 12
            else None
        )

        start_quarter = end_quarter - 3
        country_vacancy = vacancy.loc[
            vacancy["country_code"].eq(row.country_code)
            & vacancy["quarter"].between(start_quarter, end_quarter)
        ]
        vacancy_count = int(country_vacancy["value"].notna().sum())
        vacancy_rate = (
            float(country_vacancy["value"].mean())
            if vacancy_count == 4 and len(country_vacancy) == 4
            else None
        )
        statuses = sorted(
            {
                str(value)
                for value in country_vacancy["observation_status"].dropna()
                if str(value)
            }
        )
        coverage_codes = sorted(
            {
                str(value)
                for value in country_vacancy["coverage_note_code"].dropna()
                if str(value)
            }
        )
        records.append(
            {
                "country_code": row.country_code,
                "period": row.period,
                "unemployment_rate": unemployment_rate,
                "unemployment_observations": unemployment_count,
                "unemployment_coverage_status": (
                    "COMPLETE" if unemployment_rate is not None else "INCOMPLETE"
                ),
                "job_vacancy_rate": vacancy_rate,
                "job_vacancy_observations": vacancy_count,
                "job_vacancy_coverage_status": (
                    "COMPLETE" if vacancy_rate is not None else "INCOMPLETE"
                ),
                "job_vacancy_has_provisional": bool(
                    country_vacancy["is_provisional"].fillna(False).any()
                ),
                "job_vacancy_statuses": "|".join(statuses),
                "job_vacancy_coverage_note_code": "|".join(coverage_codes),
            }
        )
    return pd.DataFrame(records)


def build_quarterly_context(
    new_hire: pd.DataFrame,
    senior_hire: pd.DataFrame,
    turnover: pd.DataFrame,
    unemployment_monthly: pd.DataFrame,
    unemployment_quarterly: pd.DataFrame,
    job_vacancy_quarterly: pd.DataFrame,
) -> pd.DataFrame:
    direct_context = _direct_quarterly_external_context(
        unemployment_quarterly, job_vacancy_quarterly
    )
    new_rows = _cohort_quarterly_rows(
        new_hire,
        workforce_metric="NEW_HIRE_6M_RETENTION",
        external_context=direct_context,
    )
    senior_rows = _cohort_quarterly_rows(
        senior_hire,
        workforce_metric="SENIOR_HIRE_12M_RETENTION",
        external_context=direct_context,
    )

    turnover_rows = turnover.copy().rename(
        columns={
            "reporting_quarter": "period",
            "regretted_exits": "numerator",
            "average_active_headcount": "denominator",
            "turnover_rate": "workforce_rate",
            "window_start": "period_start",
            "window_end": "period_end",
        }
    )
    if "sample_warning" not in turnover_rows.columns:
        turnover_rows["sample_warning"] = ""
        turnover_rows.loc[
            turnover_rows["denominator"].between(0, 20, inclusive="neither"),
            "sample_warning",
        ] = "LOW_AVERAGE_HEADCOUNT"
    country_periods = turnover_rows[["country_code", "period"]].drop_duplicates()
    trailing_context = _trailing_external_context(
        unemployment_monthly, job_vacancy_quarterly, country_periods
    )
    turnover_rows = turnover_rows.merge(
        trailing_context,
        on=["country_code", "period"],
        how="left",
        validate="many_to_one",
    )
    turnover_rows["workforce_metric"] = "REGRETTED_TURNOVER_12M"
    turnover_rows["workforce_window"] = "TRAILING_12_MONTHS"
    turnover_rows["external_context_window"] = "TRAILING_12_MONTHS"
    turnover_rows["retrospective_warning"] = RETROSPECTIVE_WARNING

    columns = [
        "objective_id",
        "workforce_metric",
        "country_code",
        "period",
        "period_start",
        "period_end",
        "business_unit",
        "aggregation_level",
        "numerator",
        "denominator",
        "workforce_rate",
        "target_value",
        "target_status",
        "sample_warning",
        "workforce_window",
        "external_context_window",
        "unemployment_rate",
        "unemployment_observations",
        "unemployment_coverage_status",
        "job_vacancy_rate",
        "job_vacancy_observations",
        "job_vacancy_coverage_status",
        "job_vacancy_has_provisional",
        "job_vacancy_statuses",
        "job_vacancy_coverage_note_code",
        "retrospective_warning",
    ]
    return (
        pd.concat([new_rows, senior_rows, turnover_rows], ignore_index=True)
        .loc[:, columns]
        .sort_values(
            ["country_code", "period", "objective_id", "aggregation_level", "business_unit"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def _annual_cohort_rows(
    metric: pd.DataFrame,
    *,
    workforce_metric: str,
) -> pd.DataFrame:
    frame = metric.copy()
    frame["reference_year"] = frame["cohort_quarter"].str[:4].astype(int)
    grouped = (
        frame.groupby(
            [
                "objective_id",
                "country_code",
                "reference_year",
                "business_unit",
                "aggregation_level",
            ],
            sort=True,
            dropna=False,
        )
        .agg(
            numerator=("retained_hires", "sum"),
            denominator=("eligible_hires", "sum"),
            target_value=("target_value", "first"),
        )
        .reset_index()
    )
    grouped["workforce_rate"] = grouped["numerator"].div(
        grouped["denominator"].where(grouped["denominator"] > 0)
    )
    grouped["target_status"] = "NOT_YET_MEASURABLE"
    measurable = grouped["denominator"] > 0
    grouped.loc[
        measurable & (grouped["workforce_rate"] >= grouped["target_value"]),
        "target_status",
    ] = "MET"
    grouped.loc[
        measurable & (grouped["workforce_rate"] < grouped["target_value"]),
        "target_status",
    ] = "BELOW_TARGET"
    grouped["sample_warning"] = ""
    grouped.loc[
        grouped["denominator"].between(1, 9, inclusive="both"), "sample_warning"
    ] = "SMALL_SAMPLE"
    grouped["workforce_metric"] = workforce_metric
    grouped["annual_workforce_method"] = "SUM_NUMERATORS_DIVIDED_BY_SUM_DENOMINATORS"
    return grouped


def build_annual_inflation_context(
    new_hire: pd.DataFrame,
    senior_hire: pd.DataFrame,
    turnover: pd.DataFrame,
    inflation_annual: pd.DataFrame,
) -> pd.DataFrame:
    new_rows = _annual_cohort_rows(
        new_hire, workforce_metric="NEW_HIRE_6M_RETENTION"
    )
    senior_rows = _annual_cohort_rows(
        senior_hire, workforce_metric="SENIOR_HIRE_12M_RETENTION"
    )

    turnover_rows = turnover.loc[
        turnover["reporting_quarter"].str.endswith("Q4")
    ].copy()
    turnover_rows["reference_year"] = turnover_rows["reporting_quarter"].str[:4].astype(int)
    turnover_rows = turnover_rows.rename(
        columns={
            "regretted_exits": "numerator",
            "average_active_headcount": "denominator",
            "turnover_rate": "workforce_rate",
        }
    )
    turnover_rows["workforce_metric"] = "REGRETTED_TURNOVER_12M"
    turnover_rows["annual_workforce_method"] = "Q4_TRAILING_WINDOW_EQUALS_CALENDAR_YEAR"

    columns_before_join = [
        "objective_id",
        "workforce_metric",
        "country_code",
        "reference_year",
        "business_unit",
        "aggregation_level",
        "numerator",
        "denominator",
        "workforce_rate",
        "target_value",
        "target_status",
        "sample_warning",
        "annual_workforce_method",
    ]
    workforce = pd.concat(
        [
            new_rows.loc[:, columns_before_join],
            senior_rows.loc[:, columns_before_join],
            turnover_rows.loc[:, columns_before_join],
        ],
        ignore_index=True,
    )
    inflation = inflation_annual.rename(
        columns={
            "value": "inflation_rate",
            "provider_last_updated": "inflation_provider_last_updated",
            "observation_status": "inflation_observation_status",
        }
    )[
        [
            "country_code",
            "reference_year",
            "inflation_rate",
            "inflation_observation_status",
            "inflation_provider_last_updated",
            "retrieved_at_utc",
            "raw_sha256",
        ]
    ]
    result = workforce.merge(
        inflation,
        on=["country_code", "reference_year"],
        how="left",
        validate="many_to_one",
    )
    result["inflation_coverage_status"] = result["inflation_rate"].notna().map(
        {True: "COMPLETE", False: "MISSING"}
    )
    result["retrospective_warning"] = RETROSPECTIVE_WARNING
    return result.sort_values(
        ["country_code", "reference_year", "objective_id", "aggregation_level", "business_unit"],
        kind="stable",
    ).reset_index(drop=True)
