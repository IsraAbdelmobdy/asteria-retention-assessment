import pandas as pd
import pytest

from asteria_retention.domain.quality import (
    REQUIRED_COLUMNS,
    WorkforceContractError,
    assess_workforce_quality,
)


def employee(**overrides):
    row = {
        "employee_id": "E001",
        "country_code": "GR",
        "business_unit": "Digital",
        "job_family": "Software",
        "career_level": "Senior Leader",
        "employment_type": "Permanent",
        "hire_date": "2021-01-01",
        "termination_date": "",
        "termination_type": "",
        "regretted_exit": "",
        "source_system": "HCM_A",
        "record_updated_at": "2025-12-31",
    }
    row.update(overrides)
    return row


def test_aliases_are_normalised_without_excluding_records():
    result = assess_workforce_quality(
        pd.DataFrame([employee(country_code="EL", career_level="Sr Mgmt")])
    )

    assert len(result.analytical) == 1
    assert result.analytical.loc[0, "country_code"] == "GR"
    assert result.analytical.loc[0, "career_level"] == "Senior Leader"
    assert set(result.issues["reason_code"]) == {
        "COUNTRY_ALIAS_EL_GR",
        "CAREER_LEVEL_ALIAS",
    }


def test_invalid_chronology_is_hard_quarantined_with_visible_reason():
    result = assess_workforce_quality(
        pd.DataFrame(
            [
                employee(
                    hire_date="2022-02-01",
                    termination_date="2022-01-01",
                    termination_type="Voluntary",
                    regretted_exit="true",
                )
            ]
        )
    )

    assert result.analytical.empty
    assert result.excluded.loc[0, "exclusion_reason_codes"] == "TERMINATION_BEFORE_HIRE"
    assert result.excluded.loc[0, "exclusion_classification"] == "HARD_QUARANTINE"


def test_exact_duplicate_is_removed_deterministically():
    row = employee()
    result = assess_workforce_quality(pd.DataFrame([row, row]))

    assert len(result.analytical) == 1
    assert result.summary["exact_duplicate_rows_removed"] == 1
    assert result.issues.loc[0, "reason_code"] == "EXACT_DUPLICATE"


def test_unknown_termination_classifications_are_preserved():
    result = assess_workforce_quality(
        pd.DataFrame([employee(termination_date="2024-04-01")])
    )

    assert len(result.analytical) == 1
    assert set(result.issues["reason_code"]) == {
        "MISSING_TERMINATION_TYPE",
        "UNKNOWN_REGRETTED_CLASSIFICATION",
    }
    assert "MISSING_TERMINATION_TYPE" in result.analytical.loc[0, "quality_warning_codes"]


def test_contract_column_order_is_stable():
    result = assess_workforce_quality(pd.DataFrame([employee()]))

    assert list(result.analytical.columns[: len(REQUIRED_COLUMNS) + 1]) == [
        "source_row_number",
        *REQUIRED_COLUMNS,
    ]


def test_missing_country_is_metric_ineligible_not_hard_quarantined():
    result = assess_workforce_quality(pd.DataFrame([employee(country_code="")]))

    assert result.analytical.empty
    assert result.excluded.loc[0, "exclusion_classification"] == "METRIC_INELIGIBLE"
    assert result.excluded.loc[0, "exclusion_reason_codes"] == "MISSING_COUNTRY"


def test_missing_hire_date_is_metric_ineligible_not_hard_quarantined():
    result = assess_workforce_quality(pd.DataFrame([employee(hire_date="")]))

    assert result.analytical.empty
    assert result.excluded.loc[0, "exclusion_classification"] == "METRIC_INELIGIBLE"
    assert result.excluded.loc[0, "exclusion_reason_codes"] == "MISSING_HIRE_DATE"


def test_conflicting_employee_records_fail_validation():
    first = employee(employee_id="E-CONFLICT", business_unit="Digital")
    second = employee(employee_id="E-CONFLICT", business_unit="Finance")

    with pytest.raises(WorkforceContractError, match="fail validation"):
        assess_workforce_quality(pd.DataFrame([first, second]))
