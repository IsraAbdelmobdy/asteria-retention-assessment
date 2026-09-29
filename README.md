# Asteria retention and external signals

A small, reproducible data product for evaluating three fictional workforce-retention objectives alongside public economic indicators.

## Quick start: run the complete dashboard

From the repository root on Windows, these commands create an isolated Python environment, install the tested dependencies, prepare the complete project without requiring internet access, and open the interactive dashboard:

```cmd
python -m venv .venv
.venv\Scripts\python.exe -m pip install pip==25.0.1
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install -e . --no-deps
.venv\Scripts\python.exe -m asteria_retention run --offline
.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

The offline demonstration verifies and processes the preserved public-source responses in `tests/fixtures/replay` through the same source adapters used by the online workflow. It keeps their original retrieval timestamps and does not present them as newly downloaded data.

The dashboard lets a reviewer explore all three workforce objectives, country and business-unit results, economic relationships, data-quality evidence, source attribution, and known limitations. The `python` command must refer to Python 3.11 or newer; confirm it with `python --version` if needed.

To inspect the completed results without running Python, start with [`evidence/README.md`](evidence/README.md), which links to the reviewed analytical extracts, quality reports, source attribution, and seven dashboard screenshots.

## Problem and scope

For Asteria's six countries, the product answers three questions:

1. Were the three supplied workforce objectives met?
2. Which countries, periods, or business units may need attention?
3. Do unemployment, job vacancies, or consumer-price inflation show a useful descriptive relationship with the workforce results?

Workforce reporting covers the full 2021-2025 objective period. Pre-2021 employment records contribute only where historical headcount or turnover requires them. Unemployment and job vacancies include 2020 support history for early-2021 trailing windows. The analysis reports association and context; it does not claim that economic conditions caused workforce outcomes.

## Implemented solution

The complete local vertical slice includes:

- Manifest checksum, byte-count, and row-count verification
- Deterministic exact-duplicate removal
- Approved country and career-level normalisation
- Explicit distinction between metric ineligibility and hard quarantine
- Preservation of unknown classifications as warnings
- Analytical workforce data and quality evidence
- Six-month new-hire retention by country, hire quarter, and business unit
- Twelve-month senior-hire retention by country, hire quarter, and business unit
- Trailing-twelve-month regretted turnover by country, quarter end, and business unit

- Download and preparation of all three approved external indicators
- Frequency-safe alignment of workforce and economic periods
- Nine country-level Spearman association comparisons
- Four candidate-approved findings with interpretation limits
- DuckDB analytical storage and audit metadata
- A local Streamlit dashboard with filters, trends, relationships, quality evidence, sources, and methodology
- Online and network-independent offline workflows
- Bounded public-API retries and safe database-last failure behaviour
- A tested production mapping to ADF, lakehouse storage, Databricks, and Power BI

## Architecture

The local flow is intentionally small:

```text
Supplied workforce files + public APIs
    -> source adapters
    -> quality and domain rules
    -> canonical and analytical outputs
    -> DuckDB
    -> Streamlit dashboard
```

Adapters own source formats, domain modules own metric meaning, pipeline services coordinate the work, DuckDB stores prepared evidence, and Streamlit only presents approved results. The detailed local boundaries and the production ADF/lakehouse/Databricks/Power BI mapping are documented in `docs/architecture.md`.

## Prerequisites

- Python 3.11 or newer
- Git

## Developer setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pip==25.0.1
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

`requirements.lock` records the exact direct and indirect dependency versions used by the verified application, dashboard, and test environment. `pyproject.toml` remains the readable package contract; installing the local package with `--no-deps` prevents its broad compatibility ranges from replacing the locked versions.

## Commands available now

Run the complete online workflow with one command:

```cmd
.venv\Scripts\python.exe -m asteria_retention run
```

For a demonstration without API access, validate and reuse the previously downloaded external data:

```cmd
.venv\Scripts\python.exe -m asteria_retention run --offline
```

Both commands prepare workforce metrics, combined context, associations, and DuckDB. The online command refreshes all external indicators. Temporary network failures, rate limits, and selected server errors receive at most three attempts with short increasing waits; permanent request errors fail immediately. Offline mode makes no API calls: it validates existing cached country-period grids, or on a fresh clone it verifies and processes the three small public responses in `tests/fixtures/replay`. DuckDB is rebuilt last, and `data/output/core_run_summary.json` records stage-level success or failure.

Validate the checked-in configuration:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention validate-config
```

Verify and prepare the supplied workforce data:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention prepare-workforce
```

This writes reproducible generated files to:

- `data/canonical/analytical_workforce.csv`
- `data/output/input_integrity_report.json`
- `data/output/workforce_quality_summary.json`
- `data/output/workforce_quality_issues.csv`
- `data/output/workforce_excluded_records.csv`

Calculate the first approved retention objective:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention calculate-new-hire-retention
```

This reruns workforce preparation first, then writes:

- `data/output/new_hire_6m_retention.csv`
- `data/output/new_hire_6m_summary.json`

Calculate the second approved retention objective:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention calculate-senior-hire-retention
```

This reruns workforce preparation first, then writes:

- `data/output/senior_hire_12m_retention.csv`
- `data/output/senior_hire_12m_summary.json`

Calculate the third approved retention objective:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention calculate-regretted-turnover
```

This reruns workforce preparation first, then writes:

- `data/output/regretted_turnover_12m.csv`
- `data/output/regretted_turnover_12m_summary.json`

Download and prepare Eurostat unemployment:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention ingest-unemployment
```

This writes:

- an immutable raw JSON response under `data/raw/eurostat`
- `data/canonical/unemployment_monthly.csv`
- `data/output/unemployment_quarterly.csv`
- `data/output/unemployment_ingestion_summary.json`

The command requires internet access. It preserves retrieval and revision evidence rather than pretending that current Eurostat values are the exact historical publication vintage.

Download and preserve Eurostat job vacancies:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention ingest-job-vacancy
```

This writes:

- an immutable raw JSON response under `data/raw/eurostat`
- `data/canonical/job_vacancy_quarterly.csv`
- `data/output/job_vacancy_ingestion_summary.json`

The native quarterly values are not re-aggregated. Provisional flags and Italy's reduced-public-sector-coverage warning remain visible.

Download and preserve World Bank annual inflation:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention ingest-inflation
```

This writes:

- an immutable raw JSON response under `data/raw/world_bank`
- `data/canonical/consumer_price_inflation_annual.csv`
- `data/output/inflation_ingestion_summary.json`

The annual values are never copied into quarters or months. Missing country-years remain visible, and attribution and CC BY 4.0 licence information are retained.

Build the local analytical database after all preparation commands have run:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

This atomically creates or replaces:

- `data/output/asteria.duckdb`

The database contains `canonical`, `analytics`, and `audit` schemas. The previous working database remains unchanged if a required file is missing or a load fails.

Build the approved quarterly and annual combined context, then refresh DuckDB:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention build-combined-context
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

This creates:

- `data/output/combined_quarterly_context.csv`
- `data/output/combined_annual_inflation_context.csv`
- `data/output/combined_context_summary.json`

Unemployment and vacancies include 2020 support history so every 2021-2025 turnover quarter has a complete matching twelve-month economic window. The 2020 data does not create pre-2021 workforce objectives. Small workforce groups remain visible with warnings rather than being suppressed.

Calculate the approved workforce/economic associations, then refresh DuckDB:

```powershell
.\.venv\Scripts\python.exe -m asteria_retention analyze-associations
.\.venv\Scripts\python.exe -m asteria_retention build-database
```

This creates:

- `data/output/association_results.csv`
- `data/output/association_summary.json`

The calculation uses country totals only, reports exact Spearman rank-correlation scores, and includes explicit non-causation and repeated-country warnings.

Run the interactive dashboard after the database has been built:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

The dashboard opens locally in a browser and provides country, year, objective, and business-unit filters; workforce trends; economic relationship views; quality evidence; freshness; source attribution; and methodology. Relationship calculations remain country-level because the selected economic indicators are national.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Important documents

- `docs/requirements.md`: approved metric and quality decisions
- `docs/source-register.md`: selected indicators, API contracts, coverage, and limitations
- `docs/architecture.md`: local boundaries and the ADF/lakehouse/Databricks/Power BI production blueprint
- `docs/data-quality.md`: verified quality results and treatment explanations
- `docs/new-hire-retention.md`: first objective formula, boundaries, and reconciliation
- `docs/senior-hire-retention.md`: second objective formula, senior scope, boundaries, and reconciliation
- `docs/regretted-turnover.md`: third objective formula, month-end denominator, boundaries, and limitations
- `docs/unemployment-ingestion.md`: first external source, quarterly transformation, coverage, lag, and revision treatment
- `docs/job-vacancy-ingestion.md`: second external source, provisional flags, country coverage, lag, and dataset-version safety
- `docs/inflation-ingestion.md`: third external source, annual-frequency integrity, missing values, revisions, and attribution
- `docs/database.md`: DuckDB schemas, tables, reconciled row counts, and atomic rebuild behaviour
- `docs/combined-context.md`: quarterly and annual alignment, coverage differences, and small-group warnings
- `docs/association-analysis.md`: nine approved comparisons, Spearman method, scope, and interpretation limits
- `docs/findings.md`: candidate-approved findings, supporting evidence, and interpretation boundaries
- `docs/core-workflow.md`: online and offline one-command execution, validation, and failure behaviour
- `presentation/presentation.md`: 15-minute presentation aligned to the assessment's required agenda
- `evidence/README.md`: representative curated data, reports, analytical outputs, dashboard screenshots, and source attribution
- `AI_USAGE.md`: agent work, candidate decisions, corrections, and remaining risks

## Known limitations

- The economic comparisons are descriptive associations, not evidence that an indicator caused an employee outcome.
- Countries repeat across periods, so observations are not independent experiments.
- Senior-hire country-quarter cohorts are small; individual percentages can move sharply when one person's outcome changes.
- The supplied file has one business-unit value per employee and no transfer history, so business unit is treated as constant over the available history.
- National economic indicators may not represent the local conditions experienced by every employee or business unit.
- Public-source values use the version available when downloaded and may include revisions published after the period described.
- The 2025 six-month result contains only cohorts mature by 2025-12-31, and no 2025 twelve-month senior cohort is measurable by that date.
- The production architecture is a documented mapping, not deployed Azure, Databricks, or Power BI infrastructure.

## Data safety

All supplied workforce data is synthetic. The four original supplied artifacts are preserved under `data/input`. Raw downloads and generated data are ignored by default so large or unreviewed files are not accidentally committed. Small reviewed offline replay fixtures are committed under `tests/fixtures/replay`, and the deliberately selected reviewer-facing outputs are committed under `evidence`.

The preparation command does not modify the supplied input files.
