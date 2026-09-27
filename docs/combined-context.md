# Temporally aligned workforce and external context

Status: implemented and verified

## Purpose

The combined outputs place workforce outcomes beside economic indicators that describe the same period. They remain descriptive and retrospective; they do not claim that an economic indicator caused a workforce result.

## Quarterly context

For six- and twelve-month hire retention, unemployment and job vacancies from the hire quarter are attached to the cohort result.

For trailing-twelve-month turnover, the external window is also trailing twelve months:

- unemployment is the mean of twelve monthly values; and
- job vacancies are the mean of four quarterly values.

The external mean is emitted only when the full matching window is present. The candidate identified that 2021 Q1-Q3 turnover required 2020 economic context and approved extending unemployment and vacancies back to 2020. All turnover quarters from 2021 Q1 onward now have complete matching windows. The 2020 observations provide lookback context only; they do not create pre-2021 workforce objectives.

Verified output: 1,523 rows in `combined_quarterly_context.csv`.

## Annual inflation context

Inflation remains annual. Annual new-hire and senior-hire retention are recalculated as:

```text
sum of retained hires across the year's cohorts
------------------------------------------------
sum of eligible hires across the year's cohorts
```

Quarterly percentages are never averaged directly because cohort sizes differ.

For regretted turnover, the Q4 trailing-twelve-month result is used because its window is exactly 1 January through 31 December. That calendar-year workforce result is matched with inflation from the same country and year.

Verified output: 436 rows in `combined_annual_inflation_context.csv`, with no missing inflation matches.

## Small-group warnings

Rates remain visible and unchanged. Warnings communicate instability:

- Retention with 1-9 eligible hires: `SMALL_SAMPLE`
- Turnover with average active headcount greater than 0 but below 20: `LOW_AVERAGE_HEADCOUNT`

The quarterly output contains 774 warnings and the annual output contains 126. This high count is expected because business-unit cohorts—and especially senior-hire cohorts—are small. A warning is not an exclusion and is not evidence that the formula is wrong.

## Quality fields retained

Combined rows retain workforce numerator, denominator, rate, target status, aggregation level, and warning. They also expose external observation counts, completeness, provisional vacancy status, Italy's coverage note, and a retrospective current-vintage warning.

## Commands and outputs

```powershell
.\.venv\Scripts\python.exe -m asteria_retention build-combined-context
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

Generated files:

- `data/output/combined_quarterly_context.csv`
- `data/output/combined_annual_inflation_context.csv`
- `data/output/combined_context_summary.json`

DuckDB tables:

- `analytics.combined_quarterly_context`
- `analytics.combined_annual_inflation_context`

## Interpretation limits

- Same-period association is not causation.
- External data may have been released or revised after the workforce period.
- A trailing external window would remain missing rather than use a partial average if a future source gap appeared; the current approved period has complete coverage.
- Annual inflation is not expanded to quarters.
- Small-group results require caution even when they meet or miss a target.
