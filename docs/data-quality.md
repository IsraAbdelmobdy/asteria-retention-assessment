# Workforce data-quality evidence

Status: implemented and verified  
Input package version: 1.0  
Workforce as-of date: 2025-12-31

## Integrity result

The preparation command checks the manifest before transforming employee rows. All three declared CSV artifacts matched their expected SHA-256 checksum, byte count, and logical CSV row count.

This proves that the local inputs match the supplied assessment package. It does not prove that every value is valid; value-level rules run afterward.

## Precise terminology

- `METRIC_INELIGIBLE` means required information is missing for the approved metrics. The row is preserved in exclusion evidence but is not called contradictory or hard-quarantined.
- `HARD_QUARANTINE` means the row is contradictory or fundamentally invalid and is excluded from analysis.
- Normalisation means a known alias is converted to an approved canonical value and the row remains usable.
- A warning means the row remains usable for calculations that do not require the unknown classification.

All excluded rows remain inspectable with their source row number, employee ID, original values, classification, and reason codes. “Excluded” never means silently deleted.

## Row reconciliation

| Step | Rows | Explanation |
| --- | ---: | --- |
| Source employee-event rows | 2,407 | Exact supplied CSV content |
| Exact duplicate copies removed | 7 | First identical source row retained deterministically |
| Distinct rows after deduplication | 2,400 | One row per employee ID in this supplied package |
| Metric-ineligible rows | 14 | 9 missing country plus 5 missing hire date |
| Hard-quarantined rows | 5 | Termination before hire |
| Analytical workforce rows | 2,381 | Eligible inputs for the approved country- and time-based retention objectives |

The reconciliation is exact: `2,407 - 7 - 14 - 5 = 2,381`.

## Approved decisions and observed counts

| Condition | Count | Exact treatment |
| --- | ---: | --- |
| Exact duplicate | 7 | Keep the first identical source row; remove only the duplicate copy |
| Missing country | 9 | `METRIC_INELIGIBLE`: preserve in excluded-record evidence; exclude from the approved country-level analytical workforce and current metrics |
| Missing hire date | 5 | `METRIC_INELIGIBLE`: preserve in excluded-record evidence; exclude from time-based metrics, headcount, and therefore all three current objectives |
| Termination before hire | 5 | `HARD_QUARANTINE`: preserve as exclusion evidence and exclude because the chronology is impossible |
| Greece alias `EL` | 4 | Convert to `GR`, record the normalisation, and retain |
| Romania alias `ROM` | 4 | Convert to `RO`, record the normalisation, and retain |
| Career alias `Sr Mgmt` | 10 | Convert to `Senior Leader`, record the normalisation, and retain |
| Missing termination type | 13 | Retain where termination date is sufficient; keep type unknown and attach warning |
| Missing regretted classification on a termination | 14 | Retain where this classification is not required; keep unknown and never convert to false |

There are 71 issue records because normalisations and warnings are also evidence. An “issue” does not necessarily mean exclusion.

## Why preserve excluded records?

The 14 metric-ineligible rows have no role in the current retention calculations. They are retained only for auditability, data-quality reporting, reproducibility, and possible upstream correction.

The five hard-quarantined rows are also preserved as evidence. They cannot enter analysis because their termination date precedes their hire date.

## Generated evidence

Running `python -m asteria_retention prepare-workforce` creates:

- `data/canonical/analytical_workforce.csv`: 2,381 eligible analytical rows with source-row numbers and warning codes
- `data/output/workforce_excluded_records.csv`: all 19 excluded rows, explicitly divided into `METRIC_INELIGIBLE` and `HARD_QUARANTINE`
- `data/output/workforce_quality_issues.csv`: one row per source-row/reason combination
- `data/output/workforce_quality_summary.json`: deterministic reconciliation and counts
- `data/output/input_integrity_report.json`: expected and actual hashes, sizes, and row counts

Generated files are ignored by Git by default because they are reproducible. This document provides checked-in representative evidence; selected machine-readable outputs can be deliberately committed for the final submission.

## Scope boundary

This stage does not calculate a retention metric. It establishes which records can safely enter the approved analytical workforce and precisely why other records cannot.
