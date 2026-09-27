import pandas as pd
import pytest

from asteria_retention.domain.alignment import (
    build_annual_inflation_context,
    build_quarterly_context,
)


def cohort(objective_id, quarter, eligible, retained, target):
    return {
        "objective_id": objective_id,
        "country_code": "GR",
        "cohort_quarter": quarter,
        "business_unit": "ALL",
        "aggregation_level": "COUNTRY_TOTAL",
        "cohort_hires": eligible,
        "eligible_hires": eligible,
        "not_yet_measurable_hires": 0,
        "retained_hires": retained,
        "exited_before_anniversary": eligible - retained,
        "retention_rate": retained / eligible,
        "target_value": target,
        "target_status": "MET" if retained / eligible >= target else "BELOW_TARGET",
        "sample_warning": "SMALL_SAMPLE" if eligible < 10 else "",
    }


def external_frames():
    months = pd.period_range("2021-01", "2021-12", freq="M")
    unemployment_monthly = pd.DataFrame(
        {
            "country_code": "GR",
            "reference_period": months.astype(str),
            "value": range(1, 13),
        }
    )
    unemployment_quarterly = pd.DataFrame(
        {
            "country_code": "GR",
            "reporting_quarter": ["2021-Q1", "2021-Q2", "2021-Q3", "2021-Q4"],
            "unemployment_rate": [2.0, 5.0, 8.0, 11.0],
            "monthly_observations": [3, 3, 3, 3],
            "coverage_status": ["COMPLETE"] * 4,
        }
    )
    vacancy = pd.DataFrame(
        {
            "country_code": "GR",
            "reference_period": ["2021-Q1", "2021-Q2", "2021-Q3", "2021-Q4"],
            "value": [1.0, 2.0, 3.0, 4.0],
            "observation_status": ["", "", "p", ""],
            "is_provisional": [False, False, True, False],
            "coverage_note_code": [""] * 4,
        }
    )
    return unemployment_monthly, unemployment_quarterly, vacancy


def turnover_rows():
    return pd.DataFrame(
        [
            {
                "objective_id": "REGRETTED_TURNOVER_12M",
                "country_code": "GR",
                "reporting_quarter": quarter,
                "reporting_date": end,
                "window_start": start,
                "window_end": end,
                "business_unit": "ALL",
                "aggregation_level": "COUNTRY_TOTAL",
                "regretted_exits": 1,
                "average_active_headcount": 10.0,
                "turnover_rate": 0.1,
                "target_value": 0.075,
                "target_status": "ABOVE_TARGET",
                "sample_warning": "LOW_AVERAGE_HEADCOUNT",
            }
            for quarter, start, end in (
                ("2021-Q1", "2020-04-01", "2021-03-31"),
                ("2021-Q4", "2021-01-01", "2021-12-31"),
            )
        ]
    )


def test_cohort_uses_external_values_from_same_hire_quarter():
    unemployment_monthly, unemployment_quarterly, vacancy = external_frames()
    new_hire = pd.DataFrame([cohort("NEW_HIRE_6M", "2021-Q2", 10, 9, 0.86)])
    senior = pd.DataFrame([cohort("SENIOR_HIRE_12M", "2021-Q2", 5, 4, 0.90)])

    result = build_quarterly_context(
        new_hire,
        senior,
        turnover_rows(),
        unemployment_monthly,
        unemployment_quarterly,
        vacancy,
    )

    row = result.loc[result["objective_id"].eq("NEW_HIRE_6M")].iloc[0]
    assert row["period"] == "2021-Q2"
    assert row["unemployment_rate"] == 5.0
    assert row["job_vacancy_rate"] == 2.0
    assert row["external_context_window"] == "SAME_QUARTER"


def test_turnover_requires_complete_matching_twelve_month_external_window():
    unemployment_monthly, unemployment_quarterly, vacancy = external_frames()
    cohort_frame = pd.DataFrame(
        [cohort("NEW_HIRE_6M", "2021-Q2", 10, 9, 0.86)]
    )
    result = build_quarterly_context(
        cohort_frame,
        cohort_frame.assign(objective_id="SENIOR_HIRE_12M"),
        turnover_rows(),
        unemployment_monthly,
        unemployment_quarterly,
        vacancy,
    )
    turnover = result.loc[result["objective_id"].eq("REGRETTED_TURNOVER_12M")]
    q1 = turnover.loc[turnover["period"].eq("2021-Q1")].iloc[0]
    q4 = turnover.loc[turnover["period"].eq("2021-Q4")].iloc[0]

    assert q1["unemployment_coverage_status"] == "INCOMPLETE"
    assert pd.isna(q1["unemployment_rate"])
    assert q4["unemployment_rate"] == pytest.approx(6.5)
    assert q4["job_vacancy_rate"] == pytest.approx(2.5)
    assert q4["job_vacancy_has_provisional"]


def test_annual_retention_adds_counts_before_calculating_rate():
    new_hire = pd.DataFrame(
        [
            cohort("NEW_HIRE_6M", "2021-Q1", 1, 1, 0.86),
            cohort("NEW_HIRE_6M", "2021-Q2", 10, 8, 0.86),
        ]
    )
    senior = pd.DataFrame([cohort("SENIOR_HIRE_12M", "2021-Q1", 2, 1, 0.90)])
    inflation = pd.DataFrame(
        {
            "country_code": ["GR"],
            "reference_year": [2021],
            "value": [3.0],
            "observation_status": [""],
            "provider_last_updated": ["2026-07-13"],
            "retrieved_at_utc": ["2026-09-25T00:00:00Z"],
            "raw_sha256": ["abc"],
        }
    )

    result = build_annual_inflation_context(
        new_hire, senior, turnover_rows(), inflation
    )
    annual_new = result.loc[
        result["objective_id"].eq("NEW_HIRE_6M")
    ].iloc[0]

    assert annual_new["numerator"] == 9
    assert annual_new["denominator"] == 11
    assert annual_new["workforce_rate"] == pytest.approx(9 / 11)
    assert annual_new["inflation_rate"] == 3.0


def test_annual_turnover_uses_only_q4_calendar_year_window():
    cohort_frame = pd.DataFrame(
        [cohort("NEW_HIRE_6M", "2021-Q1", 10, 9, 0.86)]
    )
    inflation = pd.DataFrame(
        {
            "country_code": ["GR"],
            "reference_year": [2021],
            "value": [3.0],
            "observation_status": [""],
            "provider_last_updated": ["2026-07-13"],
            "retrieved_at_utc": ["2026-09-25T00:00:00Z"],
            "raw_sha256": ["abc"],
        }
    )

    result = build_annual_inflation_context(
        cohort_frame,
        cohort_frame.assign(objective_id="SENIOR_HIRE_12M"),
        turnover_rows(),
        inflation,
    )
    annual_turnover = result.loc[
        result["objective_id"].eq("REGRETTED_TURNOVER_12M")
    ]

    assert len(annual_turnover) == 1
    assert annual_turnover.iloc[0]["annual_workforce_method"] == (
        "Q4_TRAILING_WINDOW_EQUALS_CALENDAR_YEAR"
    )
