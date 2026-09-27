# Workforce and economic association analysis

Status: implemented and verified

## What this stage asks

The analysis asks a narrow question: when an economic indicator is higher, does a workforce rate generally tend to be higher, lower, or show no consistent ordering?

It uses Spearman rank correlation. In intuitive terms, each set of values is placed in order from low to high, then the two orders are compared. The score ranges from `-1` to `+1`:

- a positive score means the two measures generally rise together;
- a negative score means one generally rises while the other falls;
- a score near zero means there is little consistent ordering in this dataset.

The exact score is retained. The project does not label scores `weak`, `moderate`, or `strong`, because those labels require subjective thresholds.

## The nine comparisons

Quarterly:

- six-month new-hire retention with same-quarter unemployment and job vacancies;
- twelve-month senior-hire retention with same-quarter unemployment and job vacancies; and
- trailing-twelve-month regretted turnover with trailing unemployment and job vacancies.

Annual:

- each of the three workforce objectives with consumer-price inflation.

## Why only country totals enter the calculation

The economic indicators have one value per country and period. A country can have several business-unit workforce rows, but each would repeat the same national economic value. Including all those rows would count the same economic observation several times and make the sample look larger than it really is.

Business-unit detail remains available for the dashboard and descriptive investigation. It is simply not used to calculate these nine correlations.

## Outputs

Run:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention analyze-associations
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

This creates:

- `data/output/association_results.csv`
- `data/output/association_summary.json`
- DuckDB table `analytics.association_results`

Each result records the objective, indicator, frequency, number of usable pairs and countries, covered period, coefficient, direction, calculation status, number of warned workforce rows, and interpretation warnings.

## Verified calculation results

| Workforce objective | Indicator | Usable pairs | Spearman score |
| --- | --- | ---: | ---: |
| New-hire retention | Unemployment | 108 | -0.018 |
| New-hire retention | Job vacancies | 108 | 0.028 |
| Senior-hire retention | Unemployment | 90 | 0.093 |
| Senior-hire retention | Job vacancies | 90 | 0.063 |
| Regretted turnover | Trailing unemployment | 120 | 0.097 |
| Regretted turnover | Trailing job vacancies | 120 | -0.263 |
| Annual new-hire retention | Inflation | 30 | -0.182 |
| Annual senior-hire retention | Inflation | 24 | -0.003 |
| Annual regretted turnover | Inflation | 30 | -0.002 |

All nine calculations succeeded and cover all six countries. These are calculation outputs, not causal findings. The senior-hire quarterly comparisons require particular caution because all 90 contributing country-quarter rows carry the approved small-sample warning.

## Interpretation limits

- Correlation does not prove that the economic indicator caused the workforce result.
- Each country appears in several periods, so the rows are not fully independent experiments.
- Senior-hire cohorts are often small; their percentages can move sharply when only one person's outcome changes.
- The early 2021 trailing windows include the exceptional 2020 COVID-19 period.
- National economic conditions may not represent the local conditions experienced by each employee.
- External values are the current downloaded version and may include revisions made after the workforce period.
- A near-zero result is a valid finding: it means this dataset does not show a consistent monotonic pattern.
