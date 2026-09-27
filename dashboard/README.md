# Streamlit dashboard

The dashboard reads the prepared DuckDB database in read-only mode. It does not ingest data, clean source records, or redefine retention metrics.

From the repository root, run this explicit virtual-environment command; activation is not required:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

The local page provides:

- country, year, objective, and business-unit filters;
- auditable rates, targets, status, numerators, and denominators;
- quarterly trends and business-unit comparisons;
- filter-aware relationship views with sample size and caveats; and
- data freshness, coverage, exclusions, source attribution, and methodology.

Economic relationships always use country-total workforce rows because the indicators are national. The interface states when the business-unit filter does not apply.

If the database is missing or incomplete, the page shows a recovery message instead of a traceback. Run the core pipeline and rebuild DuckDB before refreshing the page.
