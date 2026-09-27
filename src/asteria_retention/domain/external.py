"""Pure transformations for external indicators."""

from __future__ import annotations

import pandas as pd


def aggregate_monthly_unemployment_to_quarters(monthly: pd.DataFrame) -> pd.DataFrame:
    """Create quarterly means while visibly rejecting incomplete quarters."""

    frame = monthly.copy()
    periods = pd.PeriodIndex(frame["reference_period"], freq="M")
    frame["reporting_quarter"] = periods.asfreq("Q").astype(str).str.replace(
        "Q", "-Q", regex=False
    )
    grouped = (
        frame.groupby(["country_code", "reporting_quarter"], sort=True)
        .agg(
            monthly_observations=("reference_period", "size"),
            available_monthly_values=("value", "count"),
            unemployment_rate=("value", "mean"),
            observation_statuses=(
                "observation_status",
                lambda values: "|".join(
                    sorted(
                        {
                            str(value)
                            for value in values
                            if pd.notna(value) and str(value)
                        }
                    )
                ),
            ),
            provider_dataset_updated_at=("provider_dataset_updated_at", "first"),
            retrieved_at_utc=("retrieved_at_utc", "first"),
            request_url=("request_url", "first"),
            raw_sha256=("raw_sha256", "first"),
        )
        .reset_index()
    )
    grouped["expected_monthly_observations"] = 3
    complete = (
        grouped["monthly_observations"].eq(3)
        & grouped["available_monthly_values"].eq(3)
    )
    grouped["coverage_status"] = complete.map(
        {True: "COMPLETE", False: "INCOMPLETE"}
    )
    grouped.loc[~complete, "unemployment_rate"] = pd.NA
    quarter_periods = pd.PeriodIndex(
        grouped["reporting_quarter"].str.replace("-Q", "Q", regex=False), freq="Q"
    )
    grouped["quarter_start"] = quarter_periods.start_time.strftime("%Y-%m-%d")
    grouped["quarter_end"] = quarter_periods.end_time.strftime("%Y-%m-%d")
    grouped["indicator_id"] = "UNEMPLOYMENT_RATE"
    grouped["unit_code"] = "PC_ACT"
    grouped["source_frequency"] = "monthly"
    grouped["aggregation_method"] = "arithmetic_mean_require_all_3_months"
    grouped["typical_publication_lag_days"] = 31
    grouped["availability_note"] = (
        "Retrospective current-vintage value; monthly data are typically published "
        "about 31 days after month end and may be revised."
    )
    columns = [
        "indicator_id",
        "country_code",
        "reporting_quarter",
        "quarter_start",
        "quarter_end",
        "unemployment_rate",
        "unit_code",
        "monthly_observations",
        "available_monthly_values",
        "expected_monthly_observations",
        "coverage_status",
        "observation_statuses",
        "source_frequency",
        "aggregation_method",
        "typical_publication_lag_days",
        "availability_note",
        "provider_dataset_updated_at",
        "retrieved_at_utc",
        "request_url",
        "raw_sha256",
    ]
    return grouped.loc[:, columns]
