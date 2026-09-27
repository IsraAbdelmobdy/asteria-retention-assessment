# Eurostat unemployment ingestion

Status: first external indicator implemented and verified  
Indicator ID: `UNEMPLOYMENT_RATE`  
Provider dataset: Eurostat `une_rt_m`  
Requested period: 2020-01 through 2025-12  
Workforce comparison period: 2021-01 through 2025-12

## Business meaning

The unemployment rate is the percentage of the labour force that is unemployed. It provides labour-market context: a higher rate may indicate fewer outside job opportunities, but this project will not claim that unemployment causes employee retention or turnover.

## Approved source selection

- Monthly frequency (`freq=M`)
- Percentage of the active population (`unit=PC_ACT`)
- Seasonally adjusted (`s_adj=SA`)
- Total age (`age=TOTAL`)
- Total sex (`sex=T`)
- Bulgaria, Greece, Ireland, Italy, Poland, and Romania

Eurostat uses `EL` for Greece. The canonical output retains `EL` as the provider code and maps it visibly to the project code `GR`.

## Transformation

The canonical file retains one row per country and month. The analytical output calculates each quarterly unemployment rate as the arithmetic mean of its three monthly values.

A quarter is `COMPLETE` only when all three monthly observations and values are present. An incomplete quarter retains its coverage counts but receives no calculated quarterly rate; the pipeline never silently creates a two-month mean.

## Publication delay and revisions

Eurostat states that seasonally adjusted monthly unemployment is generally published approximately 31 days after the reference month. Historical values can be revised when newer labour-force information or seasonal-adjustment calculations become available.

The implementation therefore:

- associates a value with the month it describes;
- records the typical 31-day lag and labels the result as retrospective current-vintage context;
- preserves the exact request URL, retrieval timestamp, raw response, SHA-256 checksum, provider update timestamp, and observation status;
- makes no claim that the final revised value was available during the reference period; and
- allows later reruns to produce changed values without hiding the source revision.

Official metadata: https://ec.europa.eu/eurostat/cache/metadata/en/une_rt_m_esms.htm

## Live verification

Verified on 2026-09-25 using the approved API query:

- Expected and returned monthly observations: 432
- Available monthly values: 432
- Missing monthly values: 0
- Expected and returned quarterly observations: 144
- Complete quarters: 144
- Incomplete quarters: 0
- Provider dataset update returned by the API: 2026-09-22T11:00:00+0200

The refreshed response checksum was `9e855f1b87e5cbde183494de7d3348c62709734ef10a5498e94fcc1ae1d84bb9`. The 2020 observations provide lookback context for early 2021 turnover and do not create 2020 workforce results.

## Generated files

- `data/raw/eurostat/unemployment_<retrieval>_<checksum>.json`: exact provider response
- `data/canonical/unemployment_monthly.csv`: source-preserving monthly rows
- `data/output/unemployment_quarterly.csv`: complete-coverage quarterly means
- `data/output/unemployment_ingestion_summary.json`: coverage and lineage evidence

Raw and generated files are ignored by Git by default. This avoids accidentally committing downloaded or regenerated data while keeping each local run auditable.
