# One-command core workflow

Status: implemented and verified

## Online refresh

From the repository root, run:

```cmd
.venv\Scripts\python.exe -m asteria_retention run
```

The command validates configuration and supplied inputs, prepares the workforce once, calculates all three objectives, downloads all three approved external indicators, builds combined context, calculates associations, and rebuilds DuckDB last.

Each stage name is printed while the workflow runs. If a stage fails, the command returns a non-zero exit code and names the failed stage. Every file-producing stage uses its existing atomic writer. DuckDB is not replaced unless all earlier stages complete successfully.

Online public-source requests use a bounded retry policy. Transport failures, HTTP 429, and HTTP 500, 502, 503, and 504 receive at most three attempts with waits of one and then two seconds. Other HTTP client errors fail immediately because repeating an invalid request would not correct it. If all attempts fail, the provider-specific stage error remains visible in the run summary.

## Offline refresh

```cmd
.venv\Scripts\python.exe -m asteria_retention run --offline
```

Offline mode makes no API calls. It first looks for previously prepared canonical unemployment, job-vacancy, and inflation files. When they exist, it validates required columns, duplicate keys, and the complete configured country-period grids before reuse.

When prepared external files do not exist—as on a fresh reviewer clone—offline mode processes the three small public replay responses under `tests/fixtures/replay`. It verifies each payload checksum before passing the response through the same provider adapter used online. Request URLs, historical retrieval times, and attribution remain visible and are not presented as a new download.

After either path, offline mode rebuilds quarterly unemployment from monthly data and continues with alignment, associations, and DuckDB.

Offline mode is intended for repeatable demonstrations when public APIs or internet access are unavailable. It does not pretend that cached data is newly downloaded; the original retrieval timestamps remain unchanged and visible.

## Run evidence

Both modes write `data/output/core_run_summary.json`. It records:

- online or offline mode;
- start and completion times;
- success or failure status;
- completed stages;
- the failed stage and error message, when applicable; and
- the database destination.

For offline runs, the summary also identifies whether external data came from validated local canonical files or the checked replay fixtures.

Individual stage commands remain available for focused development and troubleshooting.

## Dashboard

The core command prepares data and exits. The dashboard is a separate long-running local process:

```cmd
.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```
