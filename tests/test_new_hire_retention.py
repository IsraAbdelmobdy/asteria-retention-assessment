import pandas as pd
import pytest

from asteria_retention.domain.retention import calculate_new_hire_six_month_retention


OBJECTIVE = {
    "objective_id": "NEW_HIRE_6M",
    "objective_name": "New-hire six-month retention",
    "direction": "at_least",
    "target_value": "0.86",
    "effective_from": "2021-01-01",
    "effective_to": "2025-12-31",
}


def employee(employee_id, hire_date, termination_date="", business_unit="Digital"):
    return {
        "employee_id": employee_id,
        "country_code": "GR",
        "business_unit": business_unit,
        "hire_date": hire_date,
        "termination_date": termination_date,
    }


def country_total(result):
    return result.metrics.loc[result.metrics["aggregation_level"].eq("COUNTRY_TOTAL")].iloc[0]


def test_termination_on_anniversary_counts_as_retained():
    workforce = pd.DataFrame([employee("E1", "2024-01-15", "2024-07-15")])

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    row = country_total(result)
    assert row["eligible_hires"] == 1
    assert row["retained_hires"] == 1
    assert row["retention_rate"] == 1.0
    assert row["target_status"] == "MET"


def test_termination_day_before_anniversary_is_not_retained():
    workforce = pd.DataFrame([employee("E1", "2024-01-15", "2024-07-14")])

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    row = country_total(result)
    assert row["retained_hires"] == 0
    assert row["exited_before_anniversary"] == 1
    assert row["target_status"] == "BELOW_TARGET"


def test_calendar_month_anniversary_handles_end_of_month():
    workforce = pd.DataFrame([employee("E1", "2024-08-31", "2025-02-28")])

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    assert country_total(result)["retained_hires"] == 1


def test_immature_hire_is_not_put_in_denominator():
    workforce = pd.DataFrame([employee("E1", "2025-10-01")])

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    row = country_total(result)
    assert row["cohort_hires"] == 1
    assert row["eligible_hires"] == 0
    assert row["not_yet_measurable_hires"] == 1
    assert pd.isna(row["retention_rate"])
    assert row["target_status"] == "NOT_YET_MEASURABLE"


def test_pre_objective_hire_is_not_a_new_hire_cohort_member():
    workforce = pd.DataFrame(
        [
            employee("OLD", "2020-12-31"),
            employee("NEW", "2021-01-01"),
        ]
    )

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    assert result.summary["cohort_hires"] == 1


def test_country_total_and_business_unit_detail_reconcile():
    workforce = pd.DataFrame(
        [
            employee("E1", "2024-01-01", business_unit="Digital"),
            employee(
                "E2",
                "2024-02-01",
                termination_date="2024-03-01",
                business_unit="Sales",
            ),
        ]
    )

    result = calculate_new_hire_six_month_retention(
        workforce, OBJECTIVE, as_of_date="2025-12-31"
    )

    total = country_total(result)
    detail = result.metrics.loc[result.metrics["aggregation_level"].eq("BUSINESS_UNIT")]
    assert total["eligible_hires"] == detail["eligible_hires"].sum() == 2
    assert total["retained_hires"] == detail["retained_hires"].sum() == 1
    assert total["retention_rate"] == pytest.approx(0.5)

