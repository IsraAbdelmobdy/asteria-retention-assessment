# Senior-hire twelve-month retention

Status: second retention objective implemented and verified  
Objective ID: `SENIOR_HIRE_12M`  
Target: at least 0.90  
Workforce as-of date: 2025-12-31

## Business meaning

For senior employees hired in a country and calendar quarter, the metric asks:

> Of the senior hires who have had enough time to reach their calendar-month twelve-month anniversary, what proportion remained employed through that anniversary?

## Formula

```text
eligible senior hires retained through twelve-month anniversary
----------------------------------------------------------------
eligible senior hires who reached twelve-month anniversary
```

## Approved scope and boundary rules

- `Senior Leader` is included.
- The approved `Sr Mgmt` alias is normalised to `Senior Leader` during workforce preparation and is therefore included.
- `Manager` is not included.
- The anniversary uses calendar-month arithmetic, not 365 days.
- A termination on the twelve-month anniversary counts as retained through twelve months.
- A termination before the anniversary does not count as retained.
- A senior hire whose anniversary is after 2025-12-31 is `NOT_YET_MEASURABLE` and does not enter the denominator.
- Hires before the objective effective date of 2021-01-01 are not cohort members for this objective.
- Metric-ineligible and hard-quarantined records do not enter the analytical workforce.

## Supplied-data reconciliation

| Measure | Count |
| --- | ---: |
| Senior hires within the 2021-2025 objective period | 314 |
| Eligible senior hires that reached twelve months | 266 |
| Not yet measurable | 48 |
| Retained through twelve months | 209 |
| Exited before twelve months | 57 |
| Overall weighted retention rate | 78.57% |

The reconciliations are exact:

- `314 = 266 eligible + 48 not yet measurable`
- `266 eligible = 209 retained + 57 exited before anniversary`

The approved final finding is that twelve-month senior-hire retention is the clearest workforce concern: 209 of 266 measurable senior hires were retained, producing 78.6% against the 90% target. Every country and business unit was below target across the full measurable period, but the conclusion requires strong small-cohort caution.

Results with 1-9 eligible senior hires receive `SMALL_SAMPLE`. The rate is retained rather than suppressed. All measurable senior country-quarter cohorts fall below ten, so annual count-weighted results provide a more stable additional view.

## Output grain

`senior_hire_12m_retention.csv` contains two explicit aggregation levels:

- `COUNTRY_TOTAL`: country x hire quarter, with `business_unit=ALL`
- `BUSINESS_UNIT`: country x hire quarter x actual business unit

The supplied data produced 110 country-quarter rows and 221 observed business-unit rows. A business-unit row is emitted only where that segment had at least one senior hire in the cohort.

## Verification

Automated examples cover:

- Inclusion of `Senior Leader` and exclusion of `Manager`
- Exact-anniversary inclusion
- Day-before-anniversary exclusion
- Immature cohort exclusion from the denominator
- Reconciliation between country totals and business-unit detail
- End-to-end reconciliation of generated outputs
