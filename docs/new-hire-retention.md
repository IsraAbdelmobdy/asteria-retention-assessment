# New-hire six-month retention

Status: first retention objective implemented and verified  
Objective ID: `NEW_HIRE_6M`  
Target: at least 0.86  
Workforce as-of date: 2025-12-31

## Business meaning

For employees hired in a country and calendar quarter, the metric asks:

> Of the hires who have had enough time to reach their calendar-month six-month anniversary, what proportion remained employed through that anniversary?

## Formula

```text
eligible hires retained through six-month anniversary
------------------------------------------------------
eligible hires who reached six-month anniversary
```

The cohort quarter is the quarter containing `hire_date`. Country totals and business-unit detail are produced separately so a total is never accidentally added to its segments.

## Approved boundary rules

- The anniversary uses calendar-month arithmetic, not 182 days.
- A termination on the six-month anniversary counts as retained through six months.
- A termination before the anniversary does not count as retained.
- A hire whose anniversary is after 2025-12-31 is `NOT_YET_MEASURABLE` and does not enter the denominator.
- Hires before the objective effective date of 2021-01-01 are not new-hire cohort members for this objective.
- Metric-ineligible and hard-quarantined quality records do not enter the analytical workforce.

Examples:

| Hire | Six-month anniversary | Termination | Result |
| --- | --- | --- | --- |
| 2024-01-15 | 2024-07-15 | 2024-07-15 | Retained through anniversary |
| 2024-01-15 | 2024-07-15 | 2024-07-14 | Exited before anniversary |
| 2024-08-31 | 2025-02-28 | 2025-02-28 | Retained; calendar arithmetic handles month end |
| 2025-10-01 | 2026-04-01 | blank | Not yet measurable at 2025-12-31 |

## Target status

- `MET`: at least one eligible hire and retention rate is at least 0.86.
- `BELOW_TARGET`: at least one eligible hire and retention rate is below 0.86.
- `NOT_YET_MEASURABLE`: the cohort has hires, but none has reached the anniversary by the as-of date.

Results with 1-9 eligible hires receive `SMALL_SAMPLE`. The rate remains visible and unchanged; the warning communicates that one employee can move a small cohort's percentage substantially.

## Supplied-data reconciliation

| Measure | Count |
| --- | ---: |
| Analytical hires within the 2021-2025 objective period | 1,969 |
| Eligible hires that reached six months | 1,808 |
| Not yet measurable | 161 |
| Retained through six months | 1,576 |
| Exited before six months | 232 |
| Overall weighted retention rate | 87.17% |

The reconciliations are exact:

- `1,969 = 1,808 eligible + 161 not yet measurable`
- `1,808 eligible = 1,576 retained + 232 exited before anniversary`

The approved final finding is that six-month new-hire retention generally met its objective: 1,576 of 1,808 measurable hires were retained, producing 87.2% against the 86% target. The conclusion remains qualified because 2023 and Sales were below target, country-quarter sample sizes vary, and the 2025 result includes only cohorts mature by the as-of date.

## Output grain

`new_hire_6m_retention.csv` contains two explicit aggregation levels:

- `COUNTRY_TOTAL`: country x hire quarter, with `business_unit=ALL`
- `BUSINESS_UNIT`: country x hire quarter x actual business unit

The supplied data produced 120 country-quarter rows and 472 observed business-unit rows. A business-unit row is emitted only where that segment had at least one hire in the cohort.

## Verification

Automated examples cover:

- Exact-anniversary inclusion
- Day-before-anniversary exclusion
- End-of-month calendar arithmetic
- Immature cohort exclusion from the denominator
- Objective effective-date boundary
- Reconciliation between country totals and business-unit detail
- End-to-end reconciliation of generated outputs
