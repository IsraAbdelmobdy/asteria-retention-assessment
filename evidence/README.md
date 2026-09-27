# Representative generated evidence

This folder contains a deliberately small, reviewed evidence package for the technical assessment. It demonstrates that the reproducible pipeline produced curated data, quality and coverage diagnostics, analytical results, and a working interactive dashboard.

The evidence is not an alternative source of truth and is not read by the application. A reviewer can regenerate the complete canonical and analytical outputs with:

```cmd
.venv\Scripts\python.exe -m asteria_retention run --offline
```

## Assessment evidence map

| Assessment requirement | Included evidence | What it demonstrates |
| --- | --- | --- |
| Representative curated data | `curated/workforce_sample.csv` | Canonical workforce schema, normalised values, parsed dates, and retained warning fields |
| Quality report | `reports/workforce_quality_summary.json` | Source, deduplication, exclusion, quarantine, ineligibility, and reason-code counts |
| Coverage report | `reports/coverage_summary.json` | Quarterly and annual row counts, warning counts, and complete trailing external context |
| Analytical output | `analysis/objective_summary.csv` | Auditable headline result, numerator or event count, denominator, target, status, period, and caveat for each objective |
| Association output | `analysis/association_results.csv` | All nine approved country-level Spearman comparisons and interpretation warnings |
| Dashboard evidence | `dashboard/*.png` | All three objectives, all three economic relationship views, and the shared trust and methodology view |
| Source attribution | `source-attribution.md` | Provider, dataset, request, retrieval, terms or licence, and full source-register link |

## Selection rules

- `workforce_sample.csv` contains the first three records per canonical country after stable sorting by `country_code` and `employee_id`. This produces 18 deterministic rows and avoids manual or outcome-based selection.
- `objective_summary.csv` contains one reviewer-facing row per supplied objective. Hire-retention results aggregate every measurable approved cohort. Turnover uses the latest complete trailing window, 2025 Q4, matching the default dashboard summary.
- `association_results.csv` is included in full because the approved analysis contains only nine rows.
- The quality and coverage JSON files are copied without changing their calculated values.
- The seven screenshots use all countries, all business units, and the 2021-2025 year selection shown in the dashboard. The Trust and methodology view is shared and is therefore included once.

## Evidence provenance

- Workforce as-of date: 2025-12-31.
- Workforce objective period: 2021-2025.
- Screenshot capture date: 2026-09-27.
- Screenshots show a current online refresh performed on 2026-09-27, as displayed in the Trust and methodology view.
- The checked replay fixtures remain available under [`tests/fixtures/replay`](../tests/fixtures/replay) for network-independent regeneration. Their preserved public-source vintage is 2026-09-25.
- Full calculation definitions, source contracts, findings, limitations, and lineage are documented under [`docs`](../docs).

## Deliberate exclusions

- The DuckDB database is not included because it is binary, reproducible, and not useful for line-by-line Git review.
- Full generated canonical and analytical folders are not included because they duplicate thousands of reproducible rows.
- Bulk raw downloads are not included. Small checksum-verified replay responses provide the required network-independent source evidence.
