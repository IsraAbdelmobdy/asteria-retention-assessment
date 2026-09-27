# Eurostat job-vacancy ingestion

Status: second external indicator implemented and verified  
Indicator ID: `JOB_VACANCY_RATE`  
Provider dataset: Eurostat `jvs_q_nace2`  
Requested period: 2020-Q1 through 2025-Q4  
Workforce comparison period: 2021-Q1 through 2025-Q4

## Business meaning

The job-vacancy rate is the percentage of occupied and vacant posts that are vacant. It provides labour-demand context: a higher rate suggests employers are seeking more workers, but this project will not claim that vacancies cause employee exits or retention.

## Approved source selection

- Quarterly frequency (`freq=Q`)
- Seasonally adjusted (`s_adj=SA`)
- NACE Rev. 2 activity scope B-S (`nace_r2=B-S`)
- Total employer size class (`sizeclas=TOTAL`)
- Job-vacancy rate (`indic_em=JVR`)
- Bulgaria, Greece, Ireland, Italy, Poland, and Romania

The source is already quarterly. Values are preserved at their native frequency and are not averaged, repeated into months, or otherwise transformed. Eurostat `EL` is visibly mapped to canonical `GR` while both codes are retained.

## Provisional values and revisions

A provider status containing `p` is retained and exposed as `is_provisional=true`. Provisional observations remain usable current evidence; they are not discarded or silently presented as final.

Eurostat normally releases a flash estimate around 50 days after the quarter and fuller results around 78 days after it. Values may later be revised. Each run therefore retains the exact raw response, URL, retrieval time, checksum, provider update time, and observation status and labels the output as retrospective current-vintage context.

Official metadata: https://ec.europa.eu/eurostat/cache/metadata/en/jvs_esms.htm

## Italy coverage limitation

Eurostat states that Italy does not survey public administration and does not fully cover public institutions in education and health. Every Italy row therefore retains the unmodified provider value and receives:

`ITALY_REDUCED_PUBLIC_SECTOR_COVERAGE`

This warns users that Italy is not strictly comparable with fully covered countries. The pipeline never estimates the omitted institutions.

## Dataset-version safety

The approved historical contract is fixed to `jvs_q_nace2`, NACE Rev. 2, scope B-S. Eurostat is introducing NACE Rev. 2.1, whose categories and broad activity range are not semantically identical. The pipeline fails if configuration attempts to replace the approved dataset silently. A future migration requires a reviewed mapping, renewed coverage checks, and updated documentation.

## Live verification

Verified on 2026-09-25 using the approved API query:

- Expected and returned quarterly observations: 144
- Available quarterly values: 144
- Missing values: 0
- Provisional values: 37
- Italy rows carrying the coverage warning: 24
- Provider dataset update returned by the API: 2026-03-20T23:00:00+0100

The refreshed response checksum was `63089767b9d36b80e4a2ee148d89735834189ce51434d515b0168d775e8eb665`. The 2020 observations provide lookback context for early 2021 turnover and do not create 2020 workforce results.

## Generated files

- `data/raw/eurostat/job_vacancy_<retrieval>_<checksum>.json`: exact provider response
- `data/canonical/job_vacancy_quarterly.csv`: source-preserving quarterly observations
- `data/output/job_vacancy_ingestion_summary.json`: coverage, status, version, and lineage evidence
