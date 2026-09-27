import pandas as pd
import pytest

from asteria_retention.domain.retention import (
    calculate_regretted_turnover_twelve_month,
)


OBJECTIVE = {
    "objective_id": "REGRETTED_TURNOVER_12M",
    "objective_name": "Trailing twelve-month regretted turnover",
    "direction": "at_most",
    "target_value": "0.075",
    "effective_from": "2021-01-01",
    "effective_to": "2021-12-31",
}


def employee(
    employee_id,
    hire_date="2020-01-01",
    termination_date="",
    regretted_exit="",
    business_unit="Digital",
):
    return {
        "employee_id": employee_id,
        "country_code": "GR",
        "business_unit": business_unit,
        "hire_date": hire_date,
        "termination_date": termination_date,
        "regretted_exit": regretted_exit,
    }


def country_row(result, reporting_date="2021-03-31"):
    return result.metrics.loc[
        result.metrics["aggregation_level"].eq("COUNTRY_TOTAL")
        & result.metrics["reporting_date"].eq(reporting_date)
    ].iloc[0]


def test_window_uses_twelve_month_ends_and_pre_objective_employment():
    workforce = pd.DataFrame([employee("E1", hire_date="2019-01-01")])

    result = calculate_regretted_turnover_twelve_month(
        workforce, OBJECTIVE, as_of_date="2021-12-31"
    )

    row = country_row(result)
    assert row["window_start"] == "2020-04-01"
    assert row["window_end"] == "2021-03-31"
    assert row["month_end_observations"] == 12
    assert row["average_active_headcount"] == 1.0


def test_termination_on_month_end_counts_in_that_months_headcount():
    workforce = pd.DataFrame(
        [employee("E1", termination_date="2021-03-31", regretted_exit="true")]
    )

    result = calculate_regretted_turnover_twelve_month(
        workforce, OBJECTIVE, as_of_date="2021-12-31"
    )

    row = country_row(result)
    assert row["regretted_exits"] == 1
    assert row["average_active_headcount"] == 1.0
    assert row["turnover_rate"] == 1.0


def test_only_true_is_numerator_and_unknown_is_reported_separately():
    workforce = pd.DataFrame(
        [
            employee("TRUE", termination_date="2021-01-10", regretted_exit="true"),
            employee("FALSE", termination_date="2021-01-10", regretted_exit="false"),
            employee("UNKNOWN", termination_date="2021-01-10", regretted_exit=""),
        ]
    )

    result = calculate_regretted_turnover_twelve_month(
        workforce, OBJECTIVE, as_of_date="2021-12-31"
    )

    row = country_row(result)
    assert row["total_terminations"] == 3
    assert row["regretted_exits"] == 1
    assert row["non_regretted_exits"] == 1
    assert row["unknown_regretted_exits"] == 1


def test_country_total_and_business_units_reconcile_counts_and_headcount():
    workforce = pd.DataFrame(
        [
            employee("DIGITAL", business_unit="Digital"),
            employee(
                "SALES",
                termination_date="2021-02-01",
                regretted_exit="true",
                business_unit="Sales",
            ),
        ]
    )

    result = calculate_regretted_turnover_twelve_month(
        workforce, OBJECTIVE, as_of_date="2021-12-31"
    )

    total = country_row(result)
    detail = result.metrics.loc[
        result.metrics["aggregation_level"].eq("BUSINESS_UNIT")
        & result.metrics["reporting_date"].eq("2021-03-31")
    ]
    assert total["regretted_exits"] == detail["regretted_exits"].sum() == 1
    assert total["average_active_headcount"] == pytest.approx(
        detail["average_active_headcount"].sum()
    )


def test_target_is_met_at_or_below_seven_and_a_half_percent():
    workforce = pd.DataFrame(
        [
            employee(
                f"E{number}",
                termination_date="2021-03-31" if number < 3 else "",
                regretted_exit="true" if number < 3 else "",
            )
            for number in range(40)
        ]
    )

    result = calculate_regretted_turnover_twelve_month(
        workforce, OBJECTIVE, as_of_date="2021-12-31"
    )

    assert country_row(result)["turnover_rate"] == pytest.approx(0.075)
    assert country_row(result)["target_status"] == "MET"
