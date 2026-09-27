# Public external-data replay fixtures

These three small files preserve public API responses for network-independent review. They contain country-level economic statistics and no workforce records or personal data.

Text files in the repository have one final line ending for tool compatibility. Before replay, the loader removes that declared storage-only byte and verifies the resulting original provider payload against its recorded SHA-256 checksum. `manifest.json` also preserves each request URL and retrieval timestamp. Replay is never labelled as a new download.

The fixtures cover the complete approved grids:

- Eurostat monthly unemployment: 2020-01 through 2025-12 for six countries;
- Eurostat quarterly job vacancies: 2020-Q1 through 2025-Q4 for six countries; and
- World Bank annual consumer-price inflation: 2021 through 2025 for six countries.

World Bank data is attributed in the manifest under CC BY 4.0. Provider limitations and Eurostat reuse evidence are documented in `docs/source-register.md`.
