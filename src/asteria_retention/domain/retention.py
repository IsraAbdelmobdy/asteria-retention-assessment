"""Pure retention-metric rules based on the approved requirements contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

import pandas as pd


class RetentionContractError(ValueError):
    """Raised when metric inputs do not satisfy the approved contract."""


@dataclass(frozen=True)
class RetentionMetricResult:
    metrics: pd.DataFrame
    summary: dict[str, Any]


def _parse_required_date(value: object, field_name: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        raise RetentionContractError(f"{field_name} must be an ISO date, got {value!r}")
    return pd.Timestamp(parsed)


def _cohort_quarter(values: pd.Series) -> pd.Series:
    periods = values.dt.to_period("Q")
    return periods.map(lambda period: f"{period.year}-Q{period.quarter}").astype("string")


def calculate_new_hire_six_month_retention(
    workforce: pd.DataFrame,
    objective: Mapping[str, object],
    *,
    as_of_date: date | str,
) -> RetentionMetricResult:
    """Calculate country-quarter six-month retention and business-unit detail.

    A hire is retained when no termination is recorded before the calendar-month
    six-month anniversary. A termination on the anniversary counts as retained.
    Hires whose anniversary is after the as-of date remain not yet measurable.
    """

    return _calculate_hire_retention(
        workforce,
        objective,
        as_of_date=as_of_date,
        expected_objective_id="NEW_HIRE_6M",
        anniversary_months=6,
        senior_only=False,
    )


def calculate_senior_hire_twelve_month_retention(
    workforce: pd.DataFrame,
    objective: Mapping[str, object],
    *,
    as_of_date: date | str,
) -> RetentionMetricResult:
    """Calculate twelve-month retention for canonical Senior Leader hires.

    Manager is not part of this cohort. The quality stage normalises the
    approved ``Sr Mgmt`` alias to ``Senior Leader`` before this function runs.
    """

    return _calculate_hire_retention(
        workforce,
        objective,
        as_of_date=as_of_date,
        expected_objective_id="SENIOR_HIRE_12M",
        anniversary_months=12,
        senior_only=True,
    )


def _calculate_hire_retention(
    workforce: pd.DataFrame,
    objective: Mapping[str, object],
    *,
    as_of_date: date | str,
    expected_objective_id: str,
    anniversary_months: int,
    senior_only: bool,
) -> RetentionMetricResult:
    """Apply the shared, candidate-approved hire-cohort rules."""

    if str(objective.get("objective_id")) != expected_objective_id:
        raise RetentionContractError(f"expected objective_id {expected_objective_id}")
    if str(objective.get("direction")) != "at_least":
        raise RetentionContractError(
            f"{expected_objective_id} direction must be at_least"
        )

    required_columns = {
        "employee_id",
        "country_code",
        "business_unit",
        "hire_date",
        "termination_date",
    }
    if senior_only:
        required_columns.add("career_level")
    missing = sorted(required_columns - set(workforce.columns))
    if missing:
        raise RetentionContractError(f"workforce is missing required columns: {missing}")

    as_of = _parse_required_date(as_of_date, "as_of_date")
    effective_from = _parse_required_date(objective.get("effective_from"), "effective_from")
    effective_to = _parse_required_date(objective.get("effective_to"), "effective_to")
    target = float(objective.get("target_value"))

    frame = workforce.copy()
    frame["hire_date_parsed"] = pd.to_datetime(
        frame["hire_date"], format="%Y-%m-%d", errors="coerce"
    )
    frame["termination_date_parsed"] = pd.to_datetime(
        frame["termination_date"].replace("", pd.NA),
        format="%Y-%m-%d",
        errors="coerce",
    )
    if frame["hire_date_parsed"].isna().any():
        raise RetentionContractError(
            "analytical workforce contains a missing or invalid hire_date"
        )

    if senior_only:
        frame = frame.loc[frame["career_level"].eq("Senior Leader")].copy()

    cohort = frame.loc[
        frame["hire_date_parsed"].between(effective_from, effective_to, inclusive="both")
    ].copy()
    cohort["cohort_quarter"] = _cohort_quarter(cohort["hire_date_parsed"])
    cohort["retention_anniversary"] = cohort["hire_date_parsed"] + pd.DateOffset(
        months=anniversary_months
    )
    cohort["is_eligible"] = cohort["retention_anniversary"] <= as_of
    cohort["is_retained"] = cohort["is_eligible"] & (
        cohort["termination_date_parsed"].isna()
        | (cohort["termination_date_parsed"] >= cohort["retention_anniversary"])
    )
    cohort["exited_before_anniversary"] = cohort["is_eligible"] & ~cohort["is_retained"]

    output_columns = [
        "objective_id",
        "country_code",
        "cohort_quarter",
        "business_unit",
        "aggregation_level",
        "cohort_hires",
        "eligible_hires",
        "not_yet_measurable_hires",
        "retained_hires",
        "exited_before_anniversary",
        "retention_rate",
        "target_value",
        "target_status",
        "sample_warning",
    ]

    def aggregate(group_columns: list[str], aggregation_level: str) -> pd.DataFrame:
        grouped = (
            cohort.groupby(group_columns, dropna=False, sort=True)
            .agg(
                cohort_hires=("employee_id", "size"),
                eligible_hires=("is_eligible", "sum"),
                not_yet_measurable_hires=("is_eligible", lambda values: int((~values).sum())),
                retained_hires=("is_retained", "sum"),
                exited_before_anniversary=("exited_before_anniversary", "sum"),
            )
            .reset_index()
        )
        if "business_unit" not in group_columns:
            grouped["business_unit"] = "ALL"
        grouped["aggregation_level"] = aggregation_level
        grouped["objective_id"] = expected_objective_id
        grouped["retention_rate"] = grouped["retained_hires"].div(
            grouped["eligible_hires"].where(grouped["eligible_hires"] > 0)
        )
        grouped["target_value"] = target
        grouped["target_status"] = "NOT_YET_MEASURABLE"
        measurable = grouped["eligible_hires"] > 0
        grouped.loc[measurable & (grouped["retention_rate"] >= target), "target_status"] = "MET"
        grouped.loc[measurable & (grouped["retention_rate"] < target), "target_status"] = "BELOW_TARGET"
        grouped["sample_warning"] = ""
        grouped.loc[
            grouped["eligible_hires"].between(1, 9, inclusive="both"),
            "sample_warning",
        ] = "SMALL_SAMPLE"
        return grouped.loc[:, output_columns]

    country_total = aggregate(
        ["country_code", "cohort_quarter"], "COUNTRY_TOTAL"
    )
    business_unit_detail = aggregate(
        ["country_code", "cohort_quarter", "business_unit"],
        "BUSINESS_UNIT",
    )
    metrics = (
        pd.concat([country_total, business_unit_detail], ignore_index=True)
        .sort_values(
            ["country_code", "cohort_quarter", "aggregation_level", "business_unit"],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    total_hires = int(len(cohort))
    eligible_hires = int(cohort["is_eligible"].sum())
    retained_hires = int(cohort["is_retained"].sum())
    summary: dict[str, Any] = {
        "objective_id": expected_objective_id,
        "objective_name": str(objective.get("objective_name")),
        "as_of_date": as_of.strftime("%Y-%m-%d"),
        "effective_from": effective_from.strftime("%Y-%m-%d"),
        "effective_to": effective_to.strftime("%Y-%m-%d"),
        "target_value": target,
        "anniversary_months": anniversary_months,
        "calendar_month_anniversary": True,
        "termination_on_anniversary_counts_as_retained": True,
        "cohort_hires": total_hires,
        "eligible_hires": eligible_hires,
        "not_yet_measurable_hires": total_hires - eligible_hires,
        "retained_hires": retained_hires,
        "exited_before_anniversary": int(cohort["exited_before_anniversary"].sum()),
        "overall_retention_rate": (
            retained_hires / eligible_hires if eligible_hires else None
        ),
        "country_quarter_rows": int(len(country_total)),
        "business_unit_rows": int(len(business_unit_detail)),
    }
    if senior_only:
        summary["included_career_levels"] = ["Senior Leader"]
        summary["manager_is_senior"] = False

    return RetentionMetricResult(metrics=metrics, summary=summary)


def calculate_regretted_turnover_twelve_month(
    workforce: pd.DataFrame,
    objective: Mapping[str, object],
    *,
    as_of_date: date | str,
) -> RetentionMetricResult:
    """Calculate trailing-twelve-month regretted turnover at each quarter end."""

    objective_id = "REGRETTED_TURNOVER_12M"
    if str(objective.get("objective_id")) != objective_id:
        raise RetentionContractError(f"expected objective_id {objective_id}")
    if str(objective.get("direction")) != "at_most":
        raise RetentionContractError(f"{objective_id} direction must be at_most")

    required_columns = {
        "employee_id",
        "country_code",
        "business_unit",
        "hire_date",
        "termination_date",
        "regretted_exit",
    }
    missing = sorted(required_columns - set(workforce.columns))
    if missing:
        raise RetentionContractError(f"workforce is missing required columns: {missing}")

    as_of = _parse_required_date(as_of_date, "as_of_date")
    effective_from = _parse_required_date(objective.get("effective_from"), "effective_from")
    effective_to = _parse_required_date(objective.get("effective_to"), "effective_to")
    final_reporting_date = min(as_of, effective_to)
    target = float(objective.get("target_value"))

    frame = workforce.copy()
    frame["hire_date_parsed"] = pd.to_datetime(
        frame["hire_date"], format="%Y-%m-%d", errors="coerce"
    )
    frame["termination_date_parsed"] = pd.to_datetime(
        frame["termination_date"].replace("", pd.NA),
        format="%Y-%m-%d",
        errors="coerce",
    )
    if frame["hire_date_parsed"].isna().any():
        raise RetentionContractError(
            "analytical workforce contains a missing or invalid hire_date"
        )

    regretted = frame["regretted_exit"].fillna("").astype("string").str.strip().str.lower()
    if not regretted.isin({"", "true", "false"}).all():
        raise RetentionContractError(
            "analytical workforce contains an invalid regretted_exit classification"
        )
    frame["regretted_classification"] = regretted

    reporting_periods = pd.period_range(
        start=effective_from.to_period("Q"),
        end=final_reporting_date.to_period("Q"),
        freq="Q",
    )
    reporting_dates = [period.end_time.normalize() for period in reporting_periods]
    reporting_dates = [value for value in reporting_dates if value <= final_reporting_date]

    records: list[dict[str, object]] = []

    def append_result_rows(
        group_columns: list[str],
        aggregation_level: str,
    ) -> None:
        for group_key, group in frame.groupby(group_columns, sort=True, dropna=False):
            keys = group_key if isinstance(group_key, tuple) else (group_key,)
            dimensions = dict(zip(group_columns, keys, strict=True))
            for reporting_date in reporting_dates:
                window_start = reporting_date - pd.DateOffset(years=1) + pd.Timedelta(days=1)
                terminations = group["termination_date_parsed"].between(
                    window_start, reporting_date, inclusive="both"
                )
                regretted_exits = int(
                    (terminations & group["regretted_classification"].eq("true")).sum()
                )
                non_regretted_exits = int(
                    (terminations & group["regretted_classification"].eq("false")).sum()
                )
                unknown_regretted_exits = int(
                    (terminations & group["regretted_classification"].eq("")).sum()
                )

                month_ends = pd.date_range(window_start, reporting_date, freq="ME")
                if len(month_ends) != 12:
                    raise RetentionContractError(
                        f"expected 12 month ends for reporting date {reporting_date.date()}"
                    )
                month_end_headcounts = [
                    int(
                        (
                            (group["hire_date_parsed"] <= month_end)
                            & (
                                group["termination_date_parsed"].isna()
                                | (group["termination_date_parsed"] >= month_end)
                            )
                        ).sum()
                    )
                    for month_end in month_ends
                ]
                average_headcount = sum(month_end_headcounts) / 12
                turnover_rate = (
                    regretted_exits / average_headcount if average_headcount > 0 else None
                )
                if turnover_rate is None:
                    target_status = "NOT_MEASURABLE"
                elif turnover_rate <= target:
                    target_status = "MET"
                else:
                    target_status = "ABOVE_TARGET"

                records.append(
                    {
                        "objective_id": objective_id,
                        "country_code": dimensions["country_code"],
                        "reporting_quarter": (
                            f"{reporting_date.year}-Q{reporting_date.quarter}"
                        ),
                        "reporting_date": reporting_date.strftime("%Y-%m-%d"),
                        "window_start": window_start.strftime("%Y-%m-%d"),
                        "window_end": reporting_date.strftime("%Y-%m-%d"),
                        "business_unit": dimensions.get("business_unit", "ALL"),
                        "aggregation_level": aggregation_level,
                        "total_terminations": (
                            regretted_exits
                            + non_regretted_exits
                            + unknown_regretted_exits
                        ),
                        "regretted_exits": regretted_exits,
                        "non_regretted_exits": non_regretted_exits,
                        "unknown_regretted_exits": unknown_regretted_exits,
                        "month_end_observations": 12,
                        "average_active_headcount": average_headcount,
                        "turnover_rate": turnover_rate,
                        "target_value": target,
                        "target_status": target_status,
                        "sample_warning": (
                            "LOW_AVERAGE_HEADCOUNT"
                            if 0 < average_headcount < 20
                            else ""
                        ),
                    }
                )

    append_result_rows(["country_code"], "COUNTRY_TOTAL")
    append_result_rows(["country_code", "business_unit"], "BUSINESS_UNIT")

    metrics = pd.DataFrame(records).sort_values(
        ["country_code", "reporting_date", "aggregation_level", "business_unit"],
        kind="stable",
    ).reset_index(drop=True)
    country_total_rows = metrics["aggregation_level"].eq("COUNTRY_TOTAL")

    summary: dict[str, Any] = {
        "objective_id": objective_id,
        "objective_name": str(objective.get("objective_name")),
        "as_of_date": as_of.strftime("%Y-%m-%d"),
        "effective_from": effective_from.strftime("%Y-%m-%d"),
        "effective_to": effective_to.strftime("%Y-%m-%d"),
        "target_value": target,
        "reporting_quarters": len(reporting_dates),
        "first_reporting_date": reporting_dates[0].strftime("%Y-%m-%d"),
        "last_reporting_date": reporting_dates[-1].strftime("%Y-%m-%d"),
        "month_end_observations_per_window": 12,
        "termination_on_month_end_counts_in_headcount": True,
        "unknown_regretted_classification_is_not_imputed": True,
        "business_unit_is_treated_as_constant": True,
        "rolling_windows_overlap": True,
        "country_quarter_rows": int(country_total_rows.sum()),
        "business_unit_rows": int((~country_total_rows).sum()),
    }
    return RetentionMetricResult(metrics=metrics, summary=summary)
