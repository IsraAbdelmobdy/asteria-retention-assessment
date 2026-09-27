import pandas as pd
import pytest

from asteria_retention.domain.association import build_association_results


def quarterly_rows():
    records = []
    for objective in (
        "NEW_HIRE_6M",
        "SENIOR_HIRE_12M",
        "REGRETTED_TURNOVER_12M",
    ):
        for index, quarter in enumerate(("2021-Q1", "2021-Q2", "2021-Q3"), start=1):
            records.append(
                {
                    "objective_id": objective,
                    "aggregation_level": "COUNTRY_TOTAL",
                    "country_code": "GR",
                    "period": quarter,
                    "workforce_rate": index / 10,
                    "unemployment_rate": float(index),
                    "job_vacancy_rate": float(4 - index),
                    "sample_warning": "SMALL_SAMPLE" if index == 1 else "",
                }
            )
        records.append(
            {
                "objective_id": objective,
                "aggregation_level": "BUSINESS_UNIT",
                "country_code": "GR",
                "period": "2021-Q1",
                "workforce_rate": 0.99,
                "unemployment_rate": 1.0,
                "job_vacancy_rate": 3.0,
                "sample_warning": "",
            }
        )
    return pd.DataFrame(records)


def annual_rows():
    records = []
    for objective in (
        "NEW_HIRE_6M",
        "SENIOR_HIRE_12M",
        "REGRETTED_TURNOVER_12M",
    ):
        for index, year in enumerate((2021, 2022, 2023), start=1):
            records.append(
                {
                    "objective_id": objective,
                    "aggregation_level": "COUNTRY_TOTAL",
                    "country_code": "GR",
                    "reference_year": year,
                    "workforce_rate": index / 10,
                    "inflation_rate": float(index),
                    "sample_warning": "",
                }
            )
    return pd.DataFrame(records)


def test_builds_nine_approved_country_total_associations():
    result = build_association_results(quarterly_rows(), annual_rows())

    assert len(result) == 9
    assert set(result["workforce_scope"]) == {"COUNTRY_TOTAL"}
    assert set(result["method"]) == {"SPEARMAN_RANK_CORRELATION"}
    assert set(result["calculation_status"]) == {"CALCULATED"}
    assert set(result["countries"]) == {1}


def test_uses_rank_correlation_and_does_not_repeat_business_unit_rows():
    result = build_association_results(quarterly_rows(), annual_rows())
    new_unemployment = result.loc[
        result["objective_id"].eq("NEW_HIRE_6M")
        & result["indicator_id"].eq("UNEMPLOYMENT_RATE")
    ].iloc[0]
    new_vacancy = result.loc[
        result["objective_id"].eq("NEW_HIRE_6M")
        & result["indicator_id"].eq("JOB_VACANCY_RATE")
    ].iloc[0]

    assert new_unemployment["paired_observations"] == 3
    assert new_unemployment["coefficient"] == pytest.approx(1.0)
    assert new_unemployment["direction"] == "POSITIVE"
    assert new_unemployment["warned_workforce_rows"] == 1
    assert new_vacancy["coefficient"] == pytest.approx(-1.0)
    assert new_vacancy["direction"] == "NEGATIVE"


def test_reports_no_variation_instead_of_emitting_misleading_number():
    quarterly = quarterly_rows()
    quarterly.loc[
        quarterly["objective_id"].eq("NEW_HIRE_6M")
        & quarterly["aggregation_level"].eq("COUNTRY_TOTAL"),
        "workforce_rate",
    ] = 0.5

    result = build_association_results(quarterly, annual_rows())
    rows = result.loc[
        result["objective_id"].eq("NEW_HIRE_6M")
        & result["frequency"].eq("QUARTERLY")
    ]

    assert set(rows["calculation_status"]) == {"NO_WORKFORCE_VARIATION"}
    assert rows["coefficient"].isna().all()
    assert set(rows["direction"]) == {"NOT_CALCULATED"}
