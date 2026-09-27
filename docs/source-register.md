# External source register

Status: indicator and query contracts approved; API coverage verified  
Workforce comparison period: 2021-2025  
Eurostat support-history period: 2020-2025  
Countries: Bulgaria, Greece, Ireland, Italy, Poland, Romania

API verification access date: 2026-09-24

This register distinguishes verified provider documentation from selections that still require API-level verification.

## Selected indicators

| ID | Provider | Indicator | Lens | Native frequency | Intended workforce comparison |
| --- | --- | --- | --- | --- | --- |
| `UNEMPLOYMENT_RATE` | Eurostat | Unemployment rate | Labour supply and outside opportunities | Monthly | Quarterly mean compared with quarterly workforce results |
| `JOB_VACANCY_RATE` | Eurostat | Job-vacancy rate | Labour demand | Quarterly | Native quarter compared with quarterly workforce results |
| `CONSUMER_PRICE_INFLATION` | World Bank | Inflation, consumer prices (annual %) | Cost-of-living pressure | Annual | Annual value compared with annual aggregation of workforce results |

## Eurostat: unemployment rate

- Candidate dataset: `une_rt_m`, Unemployment by sex and age - monthly data.
- Definition: unemployed people as a percentage of the labour force; the labour force is employed plus unemployed people.
- Verified selection: total sex (`sex=T`), total age (`age=TOTAL`), percentage of active population (`unit=PC_ACT`), and seasonally adjusted monthly series (`s_adj=SA`). In this dataset, `TOTAL` is the valid total-age category; `Y15-74` is not a valid category code.
- Proposed quarterly rule: arithmetic mean of the available monthly rates in the quarter. Require all three months for a normal-quality quarterly observation; otherwise flag incomplete coverage.
- Source-shaped fields to preserve: dataset code, dimension codes, geography, time, value, observation status, load time, request URL, and raw response identity.
- Documentation: https://ec.europa.eu/eurostat/cache/metadata/en/une_rt_m_esms.htm
- API guide: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/api
- Reuse policy: Eurostat material may generally be reused with acknowledgement and disclosure of changes, subject to stated exceptions: https://ec.europa.eu/eurostat/help/copyright-notice

Coverage verification:

- Dataset update reported by the API at verification: 2026-09-22.
- Current contract observations: 6 countries x 72 months = 432.
- Returned observations: 432; no missing country-months.
- No observation-status flags were returned for the selected values.
- Eurostat uses `EL` for Greece; the canonical workforce code `GR` therefore requires an explicit provider mapping.
- Current query: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?lang=en&freq=M&unit=PC_ACT&s_adj=SA&age=TOTAL&sex=T&geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&sinceTimePeriod=2020-01&untilTimePeriod=2025-12`
- The 2020 observations support the trailing windows of 2021 turnover; workforce reporting still begins in 2021.

Implemented contract:

- Record Eurostat's typical publication lag of approximately 31 days and label the analysis as retrospective current-vintage context.
- Preserve the exact raw response, request URL, retrieval timestamp, SHA-256 checksum, provider dataset update timestamp, and observation status for every run.
- Do not claim the current revised value was available during its reference period or reconstruct an unsupported historical vintage.

## Eurostat: job-vacancy rate

- Candidate dataset: `jvs_q_nace2`, job-vacancy statistics by NACE Rev. 2 activity - quarterly data. The exact active dataset/version must be confirmed because Eurostat is introducing NACE Rev. 2.1 series.
- Definition: vacancies divided by occupied posts plus vacancies, multiplied by 100.
- Verified common activity scope: `B-S`, industry, construction and services, excluding household-employer and extra-territorial activities. The broader `A-S` scope is not complete for all six countries.
- Verified remaining dimensions: quarterly (`freq=Q`), total size class (`sizeclas=TOTAL`), and job-vacancy rate (`indic_em=JVR`).
- Approved adjustment and quarterly rule: use the seasonally adjusted series (`s_adj=SA`) and retain its native quarterly frequency. Do not transform it into monthly observations. The adjusted series is preferred because it reduces predictable recurring hiring patterns and better represents underlying labour demand for comparison with retention.
- Important limitation: Eurostat documents reduced or non-identical coverage for some countries, including Italy. Country notes must be retained and shown in methodology or quality evidence.
- Publication timing: Eurostat metadata describes flash and final releases roughly 50 and 78 days after the reference quarter, with country-specific variation.
- Documentation: https://ec.europa.eu/eurostat/cache/metadata/en/jvs_esms.htm
- Reuse policy: https://ec.europa.eu/eurostat/help/copyright-notice

Coverage verification:

- Dataset code `jvs_q_nace2` returned the full 2020-Q1 through 2025-Q4 support period and reported a dataset update of 2026-03-21.
- The approved seasonally adjusted `B-S` series has all 144 expected country-quarter observations.
- `A-S` is unsuitable as the shared contract: only 60 of 120 unadjusted and 40 of 120 seasonally adjusted observations were returned.
- The unadjusted `B-S` series returned 14 provisional flags: Bulgaria for 2023-Q1 through 2025-Q4, plus Ireland and Italy for 2025-Q4.
- The current seasonally adjusted `B-S` response returned 37 provisional (`p`) flags. Exact flags remain visible.
- Current query: `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/jvs_q_nace2?lang=en&freq=Q&s_adj=SA&nace_r2=B-S&sizeclas=TOTAL&indic_em=JVR&geo=BG&geo=EL&geo=IE&geo=IT&geo=PL&geo=RO&sinceTimePeriod=2020-Q1&untilTimePeriod=2025-Q4`
- The 2020 observations support the trailing windows of 2021 turnover; workforce reporting still begins in 2021.

Implemented contract:

- Preserve provisional flags and include provisional values as current evidence rather than discarding or silently finalising them.
- Record typical flash and fuller-result publication lags of approximately 50 and 78 days and label the analysis as retrospective current-vintage context.
- Attach `ITALY_REDUCED_PUBLIC_SECTOR_COVERAGE` to every Italy observation; do not estimate omitted public institutions.
- Lock the 2020-2025 support-history contract to `jvs_q_nace2`, NACE Rev. 2, B-S; never switch silently to NACE Rev. 2.1.
- Preserve the exact raw response, URL, retrieval timestamp, SHA-256 checksum, provider update timestamp, and observation status for every run.

## World Bank: consumer-price inflation

- Indicator code: `FP.CPI.TOTL.ZG`.
- Definition: annual percentage change in the cost to the average consumer of a basket of goods and services.
- Native frequency: annual.
- Provider: World Bank World Development Indicators / Indicators API.
- Upstream source identified in metadata: International Monetary Fund, International Financial Statistics and data files.
- Licence reported by the metadata: CC BY 4.0; provider-specific terms and attribution must be retained.
- Proposed annual rule: keep one observation per country-year. Compare with annual workforce summaries. Never expand one annual value into four independently measured quarterly observations.
- Important limitation: consumer baskets, weights, geographic coverage, and survey methods can differ between countries. Interpret within-country movement more confidently than small cross-country level differences.
- Metadata: https://databank.worldbank.org/metadataglossary/jobs/series/FP.CPI.TOTL.ZG
- API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- Licensing: https://datacatalog.worldbank.org/public-licenses

Coverage verification:

- The API returned all 30 expected observations: 6 countries x 5 years, with no missing country-years for 2021-2025.
- The API reported a last-updated date of 2026-07-13 at verification.
- Provider country codes are `BGR`, `GRC`, `IRL`, `ITA`, `POL`, and `ROU`.
- Verified query: `https://api.worldbank.org/v2/country/BGR;GRC;IRL;ITA;POL;ROU/indicator/FP.CPI.TOTL.ZG?date=2021:2025&format=json&per_page=100`

Implemented contract:

- Preserve annual frequency and never copy a value into quarters or months.
- Construct the complete country/year grid so missing observations remain visible and are never guessed.
- Record source ID, provider last-update date, raw response, request URL, retrieval timestamp, SHA-256 checksum, and observation status for every run.
- Attribute the World Bank World Development Indicators series and its underlying IMF International Financial Statistics source.
- Record the World Development Indicators CC BY 4.0 licence and state that the project retains rather than frequency-expands the source values.

## Canonical country mapping

| Canonical country | Workforce code | Eurostat code | World Bank code |
| --- | --- | --- | --- |
| Bulgaria | `BG` | `BG` | `BGR` |
| Greece | `GR` | `EL` | `GRC` |
| Ireland | `IE` | `IE` | `IRL` |
| Italy | `IT` | `IT` | `ITA` |
| Poland | `PL` | `PL` | `POL` |
| Romania | `RO` | `RO` | `ROU` |

## Frequency-integrity contract

- Monthly unemployment may become a quarterly mean, while its original monthly observations remain available in the canonical data.
- Quarterly vacancy data remains quarterly.
- Annual inflation remains annual.
- Any carried value must retain its original reference period, native frequency, status, and age. A carried value is contextual display data, not a new observation.
- Association sample sizes count independent source periods, not repeated display rows.

## Selection rationale

Together, the selected indicators provide three complementary questions:

- Unemployment: how difficult might it be for workers to find another job?
- Job vacancies: how strongly are employers seeking workers?
- Inflation: how much national cost-of-living pressure might workers experience?

These are contextual hypotheses, not causal conclusions. The supplied workforce data has no salary, engagement, performance, or local cost-of-living fields, so the analysis cannot establish the mechanism behind an association.
