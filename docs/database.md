# Local DuckDB storage

Status: implemented and verified  
Database file: `data/output/asteria.duckdb`

## Purpose

DuckDB provides one local, SQL-queryable file for prepared project data. It does not replace the original inputs, raw API responses, CSV outputs, or JSON summaries. Those files remain the source and evidence layers; the database makes application queries and later joins simpler.

## Schemas and tables

### `canonical`

| Table | Purpose | Verified rows |
| --- | --- | ---: |
| `canonical.workforce` | Quality-approved workforce records | 2,381 |
| `canonical.unemployment_monthly` | Native Eurostat monthly unemployment, including 2020 support history | 432 |
| `canonical.job_vacancy_quarterly` | Native Eurostat quarterly job vacancies, including 2020 support history | 144 |
| `canonical.inflation_annual` | Native World Bank annual inflation | 30 |

### `analytics`

| Table | Purpose | Verified rows |
| --- | --- | ---: |
| `analytics.new_hire_retention` | Six-month new-hire cohort results | 592 |
| `analytics.senior_hire_retention` | Twelve-month senior-hire cohort results | 331 |
| `analytics.regretted_turnover` | Trailing-twelve-month turnover results | 600 |
| `analytics.unemployment_quarterly` | Three-month unemployment means | 144 |
| `analytics.combined_quarterly_context` | Workforce outcomes with aligned unemployment and vacancies | 1,523 |
| `analytics.combined_annual_inflation_context` | Annual workforce outcomes with annual inflation | 436 |
| `analytics.association_results` | Nine country-total workforce/economic comparisons | 9 |

### `audit`

| Table | Purpose | Verified rows |
| --- | --- | ---: |
| `audit.workforce_quality_issues` | Normalisation, warning, exclusion, and duplicate evidence | 71 |
| `audit.workforce_excluded_records` | Metric-ineligible and hard-quarantined source records | 19 |
| `audit.table_loads` | Source file, row count, and build time for each loaded table | 13 |

`audit.table_loads` has one row for each of the thirteen file-backed tables. It does not record itself as a fourteenth load.

The rebuilt database contains fourteen tables in total: thirteen file-backed tables plus `audit.table_loads`.

## Atomic rebuild behaviour

The command validates that all thirteen required prepared CSV files exist before building. It then:

1. Creates a new DuckDB file in a temporary directory beside the destination.
2. Creates all three schemas and loads all twelve file-backed tables.
3. Queries and records every table's row count.
4. Creates and reconciles `audit.table_loads`.
5. Closes and checkpoints the temporary database.
6. Replaces the previous database only after every preceding step succeeds.

If validation or loading fails, the previous database remains unchanged. This prevents a partial database from appearing successful.

## Command

```powershell
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

The prepared workforce calculations and three external-ingestion commands must have succeeded first.

## Deliberate limits

- Raw provider JSON remains on disk and is not duplicated into relational tables.
- JSON summaries and the supplied manifest remain files.
- Association results are stored. The dashboard reads these and the combined tables directly rather than adding presentation-only database views.
- No indexes, server process, user accounts, or migration framework are introduced for this small local assessment.
