# Source attribution for representative evidence

## Supplied workforce data

The employee lifecycle events, retention objectives, data dictionary, and assessment manifest are fictional synthetic artifacts supplied with the assessment. The manifest records the seed, as-of date, row counts, sizes, and SHA-256 checksums. The originals are preserved under [`data/input`](../data/input).

## Eurostat unemployment

- Provider: Eurostat.
- Dataset: `une_rt_m`.
- Indicator: seasonally adjusted monthly unemployment rate, total sex, total age, percentage of active population.
- Coverage requested: Bulgaria, Greece, Ireland, Italy, Poland, and Romania, 2020-01 through 2025-12.
- Current evidence retrieval time: 2026-09-27T14:11:04Z.
- Provider dataset update time: 2026-09-22T11:00:00+0200.
- Current response SHA-256: `9e855f1b87e5cbde183494de7d3348c62709734ef10a5498e94fcc1ae1d84bb9`.
- Preserved replay retrieval time: 2026-09-25T18:54:02Z.
- Request URL: <https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?lang=en&freq=M&unit=PC_ACT&s_adj=SA&age=TOTAL&sex=T&geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&sinceTimePeriod=2020-01&untilTimePeriod=2025-12>
- Eurostat copyright and reuse policy: <https://ec.europa.eu/eurostat/about-us/policies/copyright>

## Eurostat job vacancies

- Provider: Eurostat.
- Dataset: `jvs_q_nace2`.
- Indicator: seasonally adjusted quarterly job-vacancy rate, NACE Rev. 2 activity scope B-S, total size class.
- Coverage requested: Bulgaria, Greece, Ireland, Italy, Poland, and Romania, 2020 Q1 through 2025 Q4.
- Current evidence retrieval time: 2026-09-27T14:11:04Z.
- Provider dataset update time: 2026-03-20T23:00:00+0100.
- Current response SHA-256: `63089767b9d36b80e4a2ee148d89735834189ce51434d515b0168d775e8eb665`.
- Preserved replay retrieval time: 2026-09-25T18:54:05Z.
- Request URL: <https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/jvs_q_nace2?lang=en&freq=Q&s_adj=SA&nace_r2=B-S&sizeclas=TOTAL&indic_em=JVR&geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&sinceTimePeriod=2020-Q1&untilTimePeriod=2025-Q4>
- Official job-vacancy metadata: <https://ec.europa.eu/eurostat/cache/metadata/en/jvs_esms.htm>
- Eurostat copyright and reuse policy: <https://ec.europa.eu/eurostat/about-us/policies/copyright>

## World Bank consumer-price inflation

- Provider: World Bank, World Development Indicators.
- Indicator: Inflation, consumer prices (annual %), code `FP.CPI.TOTL.ZG`.
- Underlying source: International Financial Statistics database, International Monetary Fund.
- Coverage requested: Bulgaria, Greece, Ireland, Italy, Poland, and Romania, 2021-2025.
- Current evidence retrieval time: 2026-09-27T14:11:05Z.
- Provider last-update date: 2026-07-13.
- Current response SHA-256: `1eb8a64d373dbe032b455a15cfc0a75cdd48bb801859691224180d7d7e3c4eab`.
- Preserved replay retrieval time: 2026-09-25T13:06:06Z.
- Request URL: <https://api.worldbank.org/v2/country/BGR;GRC;IRL;ITA;POL;ROU/indicator/FP.CPI.TOTL.ZG?date=2021%3A2025&format=json&per_page=100>
- Licence: CC BY 4.0.
- World Bank licence information: <https://datacatalog.worldbank.org/public-licenses>

The complete source-selection rationale, cadence, publication-lag treatment, country mappings, limitations, and current online retrieval evidence are documented in [`docs/source-register.md`](../docs/source-register.md).
