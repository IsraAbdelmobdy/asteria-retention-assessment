# Requirements refinement

Status: candidate-approved and implemented contract  
Approved by: candidate  
Workforce as-of date: 2025-12-31

This document separates requirements stated by the assessment from decisions made by the candidate. The decisions below are working business definitions, not claims that they were prescribed by the assessment.

## Refined business question

For Asteria's six countries, how did the three retention objectives perform over time, and do selected labour-market or economic indicators provide useful context for differences between countries and periods?

The product will describe associations and context. It will not claim that an external indicator caused a retention outcome.

## Requirements stated by the assessment

- Produce auditable measures for all three supplied retention objectives.
- Make cohort eligibility, denominators, boundary dates, censoring, and invalid-record treatment explicit.
- Join workforce outcomes to external signals without using future information.
- Explain publication lag, period meaning, mixed frequencies, and aggregation or as-of rules.
- Use at least two authoritative public providers and at least three relevant indicators.
- Obtain approximately three years of external history where supported by the source.
- Provide country, time, objective, and at least one workforce-segment filter.
- Present at least three evidence-backed findings and at least one limitation or non-finding.
- Preserve source attribution, freshness, coverage, quality exclusions, and methodology.

## Candidate-approved decisions

### Reporting grain

The main reporting grain is:

`country x calendar quarter x retention objective`

Business unit is the primary workforce segment. Additional segmentation will only be added when it remains understandable and does not produce misleadingly small groups.

### Time coverage

Workforce metrics cover the full 2021-2025 objective period. Pre-2021 employment records may contribute to headcount and turnover calculations but are not evaluated as pre-objective cohorts.

External indicators cover 2021-2025 when available; approximately three years is the minimum acceptable history. Unemployment and job vacancies additionally include 2020 as support history for the trailing-twelve-month context of early 2021 turnover. The support history does not create pre-objective workforce results. Combined analyses use the actual overlapping period and disclose any coverage difference.

### Calendar rules

- Six- and twelve-month anniversaries use calendar-month arithmetic rather than fixed day counts.
- A termination on the anniversary date counts as retained through that anniversary.
- This boundary assumes that `termination_date` is the employee's last employed day.
- A cohort member is eligible only after the required anniversary has occurred on or before 2025-12-31.
- A person whose observation window is incomplete is classified as not yet measurable, not as retained or not retained.

### New-hire six-month retention

For a country and hire quarter:

`employees retained through their six-month anniversary / eligible new hires`

An employee is eligible when the employee has a usable hire date and country, passes critical chronology checks, and has reached the six-month anniversary by the as-of date.

An eligible employee is retained when the termination date is blank or is on or after the six-month anniversary.

The objective is met when the result is at least 0.86.

### Senior-hire twelve-month retention

For a country and hire quarter:

`senior hires retained through their twelve-month anniversary / eligible senior hires`

`Senior Leader` is senior. `Sr Mgmt` is normalised to `Senior Leader` and is also senior. `Manager` is not senior.

Eligibility and retention use the same rules as six-month retention, with a twelve-month anniversary. The objective is met when the result is at least 0.90.

### Trailing twelve-month regretted turnover

For a country and quarter-end reporting date:

`regretted exits in the trailing twelve months / average active headcount in those twelve months`

Average active headcount is the arithmetic mean of the twelve month-end active-headcount values in the trailing window.

The numerator includes only a termination in the window whose `regretted_exit` value is explicitly true. A missing classification remains unknown and is never guessed. The objective is met when the result is at most 0.075.

## Data-quality policy

Every exclusion or normalisation must produce a visible reason code and appear in quality evidence.

The following terms have precise meanings:

- `METRIC_INELIGIBLE`: the source row is preserved as exclusion evidence, but it cannot enter the approved analytical workforce because a field required by the metrics is missing. It is not described as a contradictory record.
- `HARD_QUARANTINE`: the row is contradictory or fundamentally invalid and cannot safely enter analysis.
- `NORMALISE_AND_RETAIN`: replace a known alias with its approved canonical value, record the change, and retain the row.
- `RETAIN_WITH_WARNING`: retain the row for calculations that do not need the missing classification; preserve the value as unknown and attach a warning.

| Condition | Unambiguous treatment | Classification | Reason code |
| --- | --- | --- | --- |
| Exact duplicate row | Keep the first identical source row and remove only the duplicate copy | Deduplication, not quarantine | `EXACT_DUPLICATE` |
| Conflicting non-identical rows for one employee ID | Hard-quarantine the conflicting ID and fail validation; never choose one silently | `HARD_QUARANTINE` plus failed run | `CONFLICTING_EMPLOYEE_RECORDS` |
| Country code `EL` | Convert to `GR`, record the normalisation, and retain the row | `NORMALISE_AND_RETAIN` | `COUNTRY_ALIAS_EL_GR` |
| Country code `ROM` | Convert to `RO`, record the normalisation, and retain the row | `NORMALISE_AND_RETAIN` | `COUNTRY_ALIAS_ROM_RO` |
| Missing country | Preserve in excluded-record evidence, but exclude from the approved country-level analytical workforce and all current retention outputs | `METRIC_INELIGIBLE`, not hard quarantine | `MISSING_COUNTRY` |
| Missing hire date | Preserve in excluded-record evidence, but exclude from all three current objectives because cohort eligibility, anniversaries, historical active status, and headcount cannot be determined | `METRIC_INELIGIBLE`, not hard quarantine | `MISSING_HIRE_DATE` |
| Termination before hire | Preserve in excluded-record evidence and exclude from analysis because the chronology is impossible | `HARD_QUARANTINE` | `TERMINATION_BEFORE_HIRE` |
| Career level `Sr Mgmt` | Convert to `Senior Leader`, record the normalisation, and retain the row | `NORMALISE_AND_RETAIN` | `CAREER_LEVEL_ALIAS` |
| Termination with missing type | Retain for retention calculations that only need the termination date; leave type unknown and attach a warning | `RETAIN_WITH_WARNING` | `MISSING_TERMINATION_TYPE` |
| Missing regretted-exit classification | Preserve as unknown and never convert to false; retain for calculations that do not require that classification | `RETAIN_WITH_WARNING` | `UNKNOWN_REGRETTED_CLASSIFICATION` |
| Blank termination date | Treat as active at the as-of date | Valid dictionary-supported meaning | No error |
| Fixed-term employment | Include unless a later documented requirement changes the scope | Valid in-scope value | No exclusion |

For this assessment, every approved retention output is country- and time-based. Therefore, missing-country and missing-hire-date rows do not enter any of the three current objective calculations. A future metric with different requirements must make a new explicit eligibility decision rather than automatically reusing these rows.

## Temporal-alignment policy

- Cohort-retention results are contextualised using external conditions associated with the hire quarter.
- Trailing-turnover results use external context from the same trailing-twelve-month window: twelve unemployment months and four vacancy quarters are required.
- The original frequency and reference period of an external observation must be retained.
- Monthly values may be aggregated to a quarter using a documented method.
- A quarterly observation remains quarterly.
- An annual observation must never be represented as twelve newly measured monthly values.
- Publication availability and lag must be documented. Retrospective analysis must be labelled when the value was not available during the period being analysed.
- Annual cohort retention is recalculated from summed numerators and denominators, not an unweighted mean of quarterly rates.
- Annual turnover uses the Q4 trailing window because it covers the calendar year; it is joined to inflation from that country and year.
- Retention denominators from 1 through 9 receive `SMALL_SAMPLE`; turnover average headcount greater than 0 but below 20 receives `LOW_AVERAGE_HEADCOUNT`. Results are warned, not suppressed.

The approved per-indicator aggregation and publication-lag rules are documented in `docs/source-register.md`. Monthly unemployment requires all three months for a quarterly mean, job vacancies remain at their native quarterly frequency, and consumer-price inflation remains annual.

## Required output fields

Each metric result must make the calculation auditable by including at least:

- Country and reporting or cohort quarter
- Objective ID
- Numerator
- Denominator
- Calculated rate
- Target and target status
- Eligible or average-headcount count, as applicable
- Not-yet-measurable count where applicable
- Excluded-record count
- Quality or small-sample warning
- Pipeline run identifier or load timestamp

## Acceptance criteria for the metric contract

- Each objective has one written numerator and denominator.
- Calendar and exact-anniversary boundary behaviour is testable.
- Incomplete observation windows never enter a retention denominator.
- `Manager` never enters the senior cohort unless this decision is explicitly changed.
- Average headcount is based on twelve month-end observations.
- Unknown classifications are measurable as unknown and never silently imputed.
- Every excluded record has a visible reason.
- Workforce-only reporting covers 2021-2025.
- Combined reporting states its actual workforce/external overlap.

## Deliberately rejected scope for the first vertical slice

- Monthly cohort reporting, because small groups would be unstable and harder to interpret.
- Causal claims about economic indicators and employee exits.
- Predictive employee-level attrition modelling.
- Silent correction or imputation of missing business classifications.
- Treating annual data as independently measured monthly or quarterly data.
- Adding many workforce filters before the required business-unit view is reliable.

## Association-analysis policy

- Use Spearman rank correlation because the question is whether two measures tend to move in the same or opposite direction; it does not assume a straight-line relationship.
- Calculate nine comparisons: each of the three workforce objectives against unemployment and job vacancies quarterly, and against inflation annually.
- Use only `COUNTRY_TOTAL` workforce rows. Business-unit rows are excluded from correlation because repeating the same national indicator for every business unit would make the evidence look larger than it is.
- Use only complete pairs where both the workforce rate and the aligned external value exist. Report the number of pairs, countries, period, and warned workforce rows.
- Keep objectives separate because retention and turnover have different meanings and time windows.
- Report the exact coefficient and mathematical direction. Do not add arbitrary `weak`, `moderate`, or `strong` labels.
- Do not calculate a coefficient when there are fewer than two pairs or either measure has no variation.
- Treat every result as descriptive association, never causation. Countries repeat over time, small senior cohorts are noisy, national indicators may not describe local employee conditions, and current external values may include later revisions.

## Resolved implementation decisions

- Per-indicator aggregation, native-frequency, publication-lag, and revision rules are approved and recorded in `docs/source-register.md`.
- Streamlit is the approved runnable local interactive experience; the production architecture maps consumption to Power BI.
- Small reviewed provider responses are retained under `tests/fixtures/replay` with request, checksum, retrieval, terms, and attribution evidence. Bulk raw downloads and generated outputs remain ignored by default.

## Approved external-indicator scope

The candidate selected these three indicators for the first vertical slice:

1. Eurostat monthly unemployment rate: labour-supply and outside-opportunity context.
2. Eurostat quarterly job-vacancy rate: labour-demand context.
3. World Bank annual consumer-price inflation: cost-of-living context.

GDP growth was considered as the third indicator but rejected for the first vertical slice. It is a broad economic-cycle measure, overlaps more with the labour-market story already represented by unemployment and vacancies, and can be unusually difficult to interpret for Ireland. Inflation adds a more distinct and HR-relevant lens. This selection does not imply that inflation causes employee exits.

The annual inflation series will remain annual. It will be compared with appropriately aggregated annual workforce results and will not be copied into quarters as if it were independently measured four times.

The candidate also approved Eurostat's seasonally adjusted `B-S` job-vacancy series. `B-S` covers industry, construction, and services and is the broadest tested activity scope with complete 2021-2025 coverage across all six countries. Seasonal adjustment is used to reduce predictable recurring hiring patterns; provider-supplied provisional flags remain visible and are not treated as missing or silently discarded.
