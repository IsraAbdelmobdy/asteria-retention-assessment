from pathlib import Path

import pandas as pd
import pytest

from asteria_retention.dashboard_data import (
    DashboardData,
    DashboardDataError,
    filter_workforce,
    load_dashboard_data,
    metric_summary,
    relationship_summary,
    trend_summary,
)


def quarterly_frame() -> pd.DataFrame:
    records = []
    for period, numerator, denominator, unemployment in (
        ("2021-Q1", 8, 10, 5.0),
        ("2021-Q2", 9, 10, 6.0),
    ):
        records.extend(
            [
                {
                    "objective_id": "NEW_HIRE_6M",
                    "country_code": "GR",
                    "period": period,
                    "business_unit": "ALL",
                    "aggregation_level": "COUNTRY_TOTAL",
                    "numerator": numerator,
                    "denominator": denominator,
                    "workforce_rate": numerator / denominator,
                    "target_value": 0.86,
                    "sample_warning": "",
                    "unemployment_rate": unemployment,
                    "job_vacancy_rate": unemployment / 2,
                },
                {
                    "objective_id": "NEW_HIRE_6M",
                    "country_code": "GR",
                    "period": period,
                    "business_unit": "Digital",
                    "aggregation_level": "BUSINESS_UNIT",
                    "numerator": numerator - 4,
                    "denominator": denominator - 5,
                    "workforce_rate": (numerator - 4) / (denominator - 5),
                    "target_value": 0.86,
                    "sample_warning": "SMALL_SAMPLE",
                    "unemployment_rate": unemployment,
                    "job_vacancy_rate": unemployment / 2,
                },
            ]
        )
    return pd.DataFrame(records)


def dashboard_data() -> DashboardData:
    annual = pd.DataFrame(
        {
            "objective_id": ["NEW_HIRE_6M", "NEW_HIRE_6M"],
            "country_code": ["GR", "GR"],
            "reference_year": [2021, 2022],
            "aggregation_level": ["COUNTRY_TOTAL", "COUNTRY_TOTAL"],
            "workforce_rate": [0.8, 0.9],
            "inflation_rate": [2.0, 4.0],
            "sample_warning": ["", ""],
        }
    )
    empty = pd.DataFrame()
    return DashboardData(
        quarterly=quarterly_frame(),
        annual=annual,
        associations=empty,
        quality_issues=empty,
        excluded_records=empty,
        table_loads=empty,
        source_freshness=empty,
    )


def test_filter_and_summary_do_not_double_count_business_units():
    selected = filter_workforce(
        quarterly_frame(),
        objective_id="NEW_HIRE_6M",
        country_code="ALL",
        business_unit="ALL",
        start_year=2021,
        end_year=2021,
    )
    summary = metric_summary(selected, "NEW_HIRE_6M")

    assert len(selected) == 2
    assert summary is not None
    assert summary["numerator"] == 17
    assert summary["denominator"] == 20
    assert summary["rate"] == pytest.approx(0.85)
    assert summary["target_status"] == "MISSED"


def test_trend_recalculates_rate_from_counts():
    selected = filter_workforce(
        quarterly_frame(),
        objective_id="NEW_HIRE_6M",
        country_code="ALL",
        business_unit="ALL",
        start_year=2021,
        end_year=2021,
    )
    trend = trend_summary(selected)

    assert trend["workforce_rate"].tolist() == pytest.approx([0.8, 0.9])


def test_relationship_uses_country_totals_and_current_filters():
    pairs, coefficient, status = relationship_summary(
        dashboard_data(),
        objective_id="NEW_HIRE_6M",
        indicator_id="UNEMPLOYMENT_RATE",
        country_code="GR",
        start_year=2021,
        end_year=2021,
    )

    assert len(pairs) == 2
    assert coefficient == pytest.approx(1.0)
    assert status == "CALCULATED"


def test_loader_reports_missing_database(tmp_path: Path):
    with pytest.raises(DashboardDataError, match="database not found"):
        load_dashboard_data(tmp_path / "missing.duckdb")
