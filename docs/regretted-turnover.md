# Trailing twelve-month regretted turnover

Status: third retention objective implemented and verified  
Objective ID: `REGRETTED_TURNOVER_12M`  
Target: at most 0.075  
Workforce as-of date: 2025-12-31

## Business meaning

At each calendar quarter end, the metric asks:

> How many explicitly regretted exits occurred during the preceding twelve months, relative to the typical active workforce size during those months?

## Formula

```text
explicitly regretted exits in the trailing twelve months
---------------------------------------------------------
mean of the twelve month-end active headcounts
```

For example, the 2023 Q2 result uses an exit window from 2022-07-01 through 2023-06-30 and month-end headcounts from 2022-07-31 through 2023-06-30.

## Candidate-approved rules

- Results are reported for each country and quarter end from 2021 Q1 through 2025 Q4.
- The trailing window includes its first and last dates.
- The denominator is the arithmetic mean of exactly twelve month-end headcounts.
- An employee is active at month end when hired on or before that date and either not terminated or terminated on or after that date.
- A termination exactly on month end counts in that month's headcount because the termination date is treated as the last employed day.
- Only `regretted_exit=true` enters the numerator.
- `false` does not enter the numerator.
- A blank regretted classification remains unknown, does not enter the numerator, and is reported separately.
- Country totals and business-unit details are separate aggregation levels and must not be added together.
- Pre-2021 employment records may contribute to early reporting windows.

## Business-unit limitation

The source contains one business-unit value per employee and no dated transfer history. The calculation therefore treats the supplied business unit as constant throughout that employee's available employment history. This supports the required segment view without inventing transfers, but historical business-unit results may be imperfect if employees actually moved between units.

## Supplied-data output

The calculation produced:

- 20 reporting quarters
- 120 country-quarter rows: 6 countries × 20 quarters
- 480 business-unit rows: 24 observed country/business-unit combinations × 20 quarters
- 12 `ABOVE_TARGET` and 108 `MET` country-quarter results across the full period

The rolling windows overlap. Counts must not be summed across quarters because the same exit can legitimately appear in several trailing-twelve-month windows.

### Latest reporting quarter: 2025 Q4

| Country | Regretted exits | Unknown classifications | Average headcount | Turnover | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Bulgaria | 17 | 0 | 278.42 | 6.11% | MET |
| Greece | 8 | 0 | 286.08 | 2.80% | MET |
| Ireland | 15 | 1 | 240.33 | 6.24% | MET |
| Italy | 14 | 0 | 279.92 | 5.00% | MET |
| Poland | 9 | 1 | 267.17 | 3.37% | MET |
| Romania | 17 | 0 | 253.17 | 6.71% | MET |

These are verified descriptive results, not evidence that any external condition caused turnover. The approved final finding is that annual regretted turnover remained within the 7.5% objective, while the increase to 5.0% in 2025 and the 12 above-target country-quarter observations remain monitoring signals.

## Output fields

Every result includes the reporting date, exact window boundaries, total terminations, regretted exits, non-regretted exits, unknown classifications, number of month-end observations, average active headcount, rate, target, and target status.

Results with average active headcount greater than zero but below 20 receive `LOW_AVERAGE_HEADCOUNT`. The rate remains visible and unchanged; the warning shows that one exit can move a small group's percentage substantially.

## Verification

Automated examples cover:

- A 12-month window containing exactly twelve month ends
- Use of pre-objective employment history in headcount
- Inclusion in headcount when termination occurs exactly on month end
- Separate true, false, and unknown regretted classifications
- Reconciliation of country totals with business-unit details
- Inclusive target behaviour at exactly 7.5%
- End-to-end output counts using the supplied data
