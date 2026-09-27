"""Auditable workforce quality and canonicalisation rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = (
    "employee_id",
    "country_code",
    "business_unit",
    "job_family",
    "career_level",
    "employment_type",
    "hire_date",
    "termination_date",
    "termination_type",
    "regretted_exit",
    "source_system",
    "record_updated_at",
)

CANONICAL_COUNTRIES = {"BG", "GR", "IE", "IT", "PL", "RO"}
COUNTRY_ALIASES = {"EL": "GR", "ROM": "RO"}
CAREER_LEVEL_ALIASES = {"Sr Mgmt": "Senior Leader"}
VALID_REGRETTED_VALUES = {"", "true", "false"}
METRIC_INELIGIBLE = "METRIC_INELIGIBLE"
HARD_QUARANTINE = "HARD_QUARANTINE"

ISSUE_COLUMNS = (
    "source_row_number",
    "employee_id",
    "reason_code",
    "severity",
    "action",
    "field_name",
    "original_value",
    "replacement_value",
    "message",
)


class WorkforceContractError(ValueError):
    """Raised when the workforce file does not have the required schema."""


@dataclass(frozen=True)
class WorkforceQualityResult:
    analytical: pd.DataFrame
    excluded: pd.DataFrame
    issues: pd.DataFrame
    summary: dict[str, Any]


def _blank(series: pd.Series) -> pd.Series:
    return series.fillna("").str.strip().eq("")


def _add_issues(
    issues: list[dict[str, object]],
    frame: pd.DataFrame,
    mask: pd.Series,
    *,
    reason_code: str,
    severity: str,
    action: str,
    field_name: str,
    message: str,
    replacement_value: str = "",
) -> None:
    for _, row in frame.loc[mask].iterrows():
        issues.append(
            {
                "source_row_number": int(row["source_row_number"]),
                "employee_id": str(row["employee_id"]),
                "reason_code": reason_code,
                "severity": severity,
                "action": action,
                "field_name": field_name,
                "original_value": str(row[field_name]),
                "replacement_value": replacement_value,
                "message": message,
            }
        )


def assess_workforce_quality(events: pd.DataFrame) -> WorkforceQualityResult:
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(events.columns))
    unexpected_columns = sorted(set(events.columns) - set(REQUIRED_COLUMNS))
    if missing_columns or unexpected_columns:
        raise WorkforceContractError(
            f"schema mismatch; missing={missing_columns}, unexpected={unexpected_columns}"
        )

    frame = events.loc[:, REQUIRED_COLUMNS].copy()
    for column in REQUIRED_COLUMNS:
        frame[column] = frame[column].fillna("").astype("string").str.strip()
    frame.insert(0, "source_row_number", range(2, len(frame) + 2))

    issues: list[dict[str, object]] = []
    exclusion_reasons: dict[int, set[str]] = {}
    exclusion_classifications: dict[int, set[str]] = {}

    duplicate_mask = frame.duplicated(subset=list(REQUIRED_COLUMNS), keep="first")
    _add_issues(
        issues,
        frame,
        duplicate_mask,
        reason_code="EXACT_DUPLICATE",
        severity="warning",
        action="deduplicate",
        field_name="employee_id",
        message="Exact duplicate removed; the first source row was retained.",
    )
    duplicate_rows_removed = int(duplicate_mask.sum())
    frame = frame.loc[~duplicate_mask].copy()

    def exclude(mask: pd.Series, reason_code: str, classification: str) -> None:
        for row_number in frame.loc[mask, "source_row_number"]:
            exclusion_reasons.setdefault(int(row_number), set()).add(reason_code)
            exclusion_classifications.setdefault(int(row_number), set()).add(classification)

    conflicting_mask = frame.duplicated(subset=["employee_id"], keep=False) & ~_blank(
        frame["employee_id"]
    )
    _add_issues(
        issues,
        frame,
        conflicting_mask,
        reason_code="CONFLICTING_EMPLOYEE_RECORDS",
        severity="error",
        action="hard_quarantine_and_fail_validation",
        field_name="employee_id",
        message="Employee ID has multiple non-identical source records.",
    )
    if conflicting_mask.any():
        conflicting_ids = sorted(frame.loc[conflicting_mask, "employee_id"].unique())
        raise WorkforceContractError(
            "conflicting non-identical records require hard quarantine and fail validation; "
            f"employee_ids={conflicting_ids}"
        )

    missing_employee_mask = _blank(frame["employee_id"])
    _add_issues(
        issues,
        frame,
        missing_employee_mask,
        reason_code="MISSING_EMPLOYEE_ID",
        severity="error",
        action="hard_quarantine",
        field_name="employee_id",
        message="Stable employee identifier is required.",
    )
    exclude(missing_employee_mask, "MISSING_EMPLOYEE_ID", HARD_QUARANTINE)

    for alias, canonical in COUNTRY_ALIASES.items():
        mask = frame["country_code"].eq(alias)
        _add_issues(
            issues,
            frame,
            mask,
            reason_code=f"COUNTRY_ALIAS_{alias}_{canonical}",
            severity="info",
            action="normalise",
            field_name="country_code",
            replacement_value=canonical,
            message=f"Provider/source alias {alias} normalised to {canonical}.",
        )
        frame.loc[mask, "country_code"] = canonical

    missing_country_mask = _blank(frame["country_code"])
    _add_issues(
        issues,
        frame,
        missing_country_mask,
        reason_code="MISSING_COUNTRY",
        severity="error",
        action="exclude_from_country_metrics",
        field_name="country_code",
        message="Country is required for the approved country-level grain.",
    )
    exclude(missing_country_mask, "MISSING_COUNTRY", METRIC_INELIGIBLE)

    unknown_country_mask = ~missing_country_mask & ~frame["country_code"].isin(
        CANONICAL_COUNTRIES
    )
    _add_issues(
        issues,
        frame,
        unknown_country_mask,
        reason_code="UNKNOWN_COUNTRY",
        severity="error",
        action="hard_quarantine",
        field_name="country_code",
        message="Country code is outside the approved six-country scope.",
    )
    exclude(unknown_country_mask, "UNKNOWN_COUNTRY", HARD_QUARANTINE)

    for alias, canonical in CAREER_LEVEL_ALIASES.items():
        mask = frame["career_level"].eq(alias)
        _add_issues(
            issues,
            frame,
            mask,
            reason_code="CAREER_LEVEL_ALIAS",
            severity="info",
            action="normalise",
            field_name="career_level",
            replacement_value=canonical,
            message=f"Career level {alias} normalised to {canonical}.",
        )
        frame.loc[mask, "career_level"] = canonical

    parsed_dates: dict[str, pd.Series] = {}
    for column in ("hire_date", "termination_date", "record_updated_at"):
        nonblank = ~_blank(frame[column])
        parsed = pd.to_datetime(frame[column].where(nonblank), format="%Y-%m-%d", errors="coerce")
        parsed_dates[column] = parsed
        invalid_mask = nonblank & parsed.isna()
        reason_code = f"INVALID_{column.upper()}"
        _add_issues(
            issues,
            frame,
            invalid_mask,
            reason_code=reason_code,
            severity="error",
            action="hard_quarantine",
            field_name=column,
            message=f"{column} is not a valid ISO calendar date.",
        )
        exclude(invalid_mask, reason_code, HARD_QUARANTINE)

    missing_hire_mask = _blank(frame["hire_date"])
    _add_issues(
        issues,
        frame,
        missing_hire_mask,
        reason_code="MISSING_HIRE_DATE",
        severity="error",
        action="exclude_from_time_metrics_and_headcount",
        field_name="hire_date",
        message="Hire date is required for cohort and headcount calculations.",
    )
    exclude(missing_hire_mask, "MISSING_HIRE_DATE", METRIC_INELIGIBLE)

    chronology_mask = (
        parsed_dates["hire_date"].notna()
        & parsed_dates["termination_date"].notna()
        & (parsed_dates["termination_date"] < parsed_dates["hire_date"])
    )
    _add_issues(
        issues,
        frame,
        chronology_mask,
        reason_code="TERMINATION_BEFORE_HIRE",
        severity="error",
        action="hard_quarantine",
        field_name="termination_date",
        message="Termination date occurs before hire date.",
    )
    exclude(chronology_mask, "TERMINATION_BEFORE_HIRE", HARD_QUARANTINE)

    missing_type_mask = parsed_dates["termination_date"].notna() & _blank(
        frame["termination_type"]
    )
    _add_issues(
        issues,
        frame,
        missing_type_mask,
        reason_code="MISSING_TERMINATION_TYPE",
        severity="warning",
        action="preserve_unknown_type",
        field_name="termination_type",
        message="Termination is retained for retention calculations, but its type remains unknown.",
    )

    missing_regretted_mask = parsed_dates["termination_date"].notna() & _blank(
        frame["regretted_exit"]
    )
    _add_issues(
        issues,
        frame,
        missing_regretted_mask,
        reason_code="UNKNOWN_REGRETTED_CLASSIFICATION",
        severity="warning",
        action="preserve_unknown",
        field_name="regretted_exit",
        message="Regretted-exit classification is unknown and was not guessed.",
    )

    invalid_regretted_mask = ~frame["regretted_exit"].isin(VALID_REGRETTED_VALUES)
    _add_issues(
        issues,
        frame,
        invalid_regretted_mask,
        reason_code="INVALID_REGRETTED_CLASSIFICATION",
        severity="error",
        action="hard_quarantine",
        field_name="regretted_exit",
        message="Regretted-exit value must be true, false, or blank.",
    )
    exclude(invalid_regretted_mask, "INVALID_REGRETTED_CLASSIFICATION", HARD_QUARANTINE)

    excluded_row_numbers = set(exclusion_reasons)
    excluded_mask = frame["source_row_number"].isin(excluded_row_numbers)

    excluded = frame.loc[excluded_mask].copy()
    excluded["exclusion_reason_codes"] = excluded["source_row_number"].map(
        lambda row_number: "|".join(sorted(exclusion_reasons[int(row_number)]))
    )
    excluded["exclusion_classification"] = excluded["source_row_number"].map(
        lambda row_number: (
            HARD_QUARANTINE
            if HARD_QUARANTINE in exclusion_classifications[int(row_number)]
            else METRIC_INELIGIBLE
        )
    )

    analytical = frame.loc[~excluded_mask].copy()
    warning_codes: dict[int, set[str]] = {}
    for issue in issues:
        if issue["severity"] == "warning":
            warning_codes.setdefault(int(issue["source_row_number"]), set()).add(
                str(issue["reason_code"])
            )
    analytical["quality_warning_codes"] = analytical["source_row_number"].map(
        lambda row_number: "|".join(sorted(warning_codes.get(int(row_number), set())))
    )

    issues_frame = pd.DataFrame(issues, columns=ISSUE_COLUMNS)
    if not issues_frame.empty:
        issues_frame = issues_frame.sort_values(
            ["source_row_number", "reason_code"], kind="stable"
        ).reset_index(drop=True)

    issue_counts = {
        str(reason): int(count)
        for reason, count in issues_frame["reason_code"].value_counts().sort_index().items()
    }
    summary: dict[str, Any] = {
        "input_rows": int(len(events)),
        "exact_duplicate_rows_removed": duplicate_rows_removed,
        "rows_after_deduplication": int(len(frame)),
        "analytical_rows": int(len(analytical)),
        "excluded_rows": int(len(excluded)),
        "metric_ineligible_rows": int(
            excluded["exclusion_classification"].eq(METRIC_INELIGIBLE).sum()
        ),
        "hard_quarantined_rows": int(
            excluded["exclusion_classification"].eq(HARD_QUARANTINE).sum()
        ),
        "quality_issue_records": int(len(issues_frame)),
        "issue_counts": issue_counts,
    }

    return WorkforceQualityResult(
        analytical=analytical.reset_index(drop=True),
        excluded=excluded.reset_index(drop=True),
        issues=issues_frame,
        summary=summary,
    )
