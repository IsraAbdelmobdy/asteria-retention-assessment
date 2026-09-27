# World Bank consumer-price inflation ingestion

Status: third external indicator implemented and verified  
Indicator ID: `CONSUMER_PRICE_INFLATION`  
Provider indicator: `FP.CPI.TOTL.ZG`  
Requested period: 2021 through 2025

## Business meaning

The indicator describes the annual percentage change in consumer prices for an average basket of goods and services. It provides cost-of-living context, but it does not mean every product, employee, or household experienced the same change, and it cannot establish a causal effect on retention.

## Approved frequency treatment

The World Bank supplies one observation per country and year. The pipeline preserves that native annual frequency:

- 6 countries × 5 years = 30 canonical rows;
- no annual value is copied into quarters or months; and
- later combined analysis must use a deliberately defined annual workforce summary rather than pretending one annual observation is four independent measurements.

## Country mapping

| World Bank | Canonical |
| --- | --- |
| `BGR` | `BG` |
| `GRC` | `GR` |
| `IRL` | `IE` |
| `ITA` | `IT` |
| `POL` | `PL` |
| `ROU` | `RO` |

Both codes remain in the canonical output.

## Missing values and revisions

The parser constructs the complete expected country/year grid. A missing source observation therefore remains as a visible row with an empty value; it is never removed, copied from another year, or estimated.

World Development Indicators historical values may change when its database is updated. There is no invented fixed publication-lag number. Every run records the reference year, provider last-update date, retrieval time, URL, raw response, checksum, and observation status and labels the result as current-vintage retrospective evidence.

World Bank revision guidance: https://datahelpdesk.worldbank.org/knowledgebase/articles/114939-how-are-revisions-managed

## Attribution and licence

Source: World Bank, World Development Indicators, “Inflation, consumer prices (annual %)” (`FP.CPI.TOTL.ZG`). Underlying source: International Financial Statistics database, International Monetary Fund. Licensed under CC BY 4.0. Annual values were retained and were not expanded to quarters or months.

Indicator metadata: https://api.worldbank.org/v2/indicator/FP.CPI.TOTL.ZG?format=json  
Dataset licence: https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators

## Live verification

Verified on 2026-09-25 using the approved API query:

- Expected and canonical annual rows: 30
- Source observations returned: 30
- Available annual values: 30
- Missing annual values: 0
- Source ID: `2`, World Development Indicators
- Provider last-update date returned by the API: 2026-07-13

The verification response checksum was `1eb8a64d373dbe032b455a15cfc0a75cdd48bb801859691224180d7d7e3c4eab`. This identifies that verification response only; the candidate's later run records its own current response evidence.

## Generated files

- `data/raw/world_bank/inflation_<retrieval>_<checksum>.json`: exact provider response
- `data/canonical/consumer_price_inflation_annual.csv`: complete annual country/year grid
- `data/output/inflation_ingestion_summary.json`: coverage, attribution, frequency, and lineage evidence
