# AI usage record

This file records meaningful use of an AI coding agent, candidate direction, verification, rejected or changed suggestions, and remaining risks. It intentionally does not contain full chat transcripts, secrets, or sensitive information.

## Tool and model disclosure

- AI tool: OpenAI Codex desktop coding agent.
- Model: GPT-5.
- Supporting local tools: PowerShell, Python, pytest, DuckDB, Streamlit test utilities, and browser-based visual inspection.
- Working method: the candidate approved material contracts and interpretations incrementally; the agent inspected data, proposed options, drafted implementation and documentation, and ran verification. The candidate challenged unclear or incorrect proposals and retained responsibility for the submitted work.

## Candidate-reported effort

Completed incrementally over several days, with approximately 20 hours of active work.

## How to read this chronological record

Each stage records the state and risks that existed at that point in development. Earlier statements such as “not yet implemented” are retained as historical evidence rather than rewritten after the fact. Their current resolution is:

- All three metric implementations, external sources, temporal rules, associations, findings, dashboard, core workflow, production mapping, offline replay, API retries, dependency lock, and presentation are complete and verified.
- Streamlit was approved as the local interactive experience, while Power BI remains the production consumption mapping.
- Initial data-quality counts were reproduced by the implemented pipeline and automated tests.
- The initial 2021-only economic window was corrected to include 2020 unemployment and vacancy support history after candidate challenge.
- The repository was published for reviewer access. A candidate-run fresh-clone rehearsal exposed Windows line-ending conversion in checksum-protected replay fixtures; the repository now fixes their checkout format, and the remaining submission task is to push and repeat that clean-clone check.

## Stage 1: assessment inspection and requirements refinement

### Agent contribution

- Inspected the assessment HTML and the supplied manifest, dictionary, workforce events, and retention-objectives data without modifying the source files.
- Summarised the explicit Software Emphasis requirements separately from recommendations.
- Profiled the supplied workforce data and identified duplicates, aliases, missing values, invalid chronology, and incomplete observation windows.
- Proposed an initial metric contract, quality policy, reporting grain, and implementation approach for candidate review.

### Candidate direction and decisions

The candidate approved the following contract:

1. Quarterly country-level reporting.
2. Calendar-month anniversaries.
3. Termination on the anniversary counts as retained through that anniversary.
4. `Senior Leader` and normalised `Sr Mgmt` count as senior; `Manager` does not.
5. Twelve month-end headcounts form the regretted-turnover denominator.
6. Business unit is the primary segment.
7. Invalid records are excluded with visible reason codes.
8. Missing classifications remain unknown and are never guessed.

The candidate also approved full workforce reporting across the 2021-2025 objective period and the use of pre-2021 records only where needed for later headcount or turnover calculations.

### Candidate challenge that changed the proposal

The candidate challenged wording that appeared to limit workforce analysis to approximately three years. This exposed an unclear distinction in the agent's proposal between the assessment's external-data minimum and the workforce-analysis period.

The proposal was corrected as follows:

- Workforce metrics cover the full 2021-2025 objective period.
- External indicators should also cover 2021-2025 where available.
- Approximately three years is treated as a minimum external-history expectation, not a maximum.
- If an external indicator has shorter coverage, only the combined comparison uses the overlapping period; earlier valid workforce results remain visible.

This correction was accepted by the candidate and incorporated into `docs/requirements.md`.

### Human validation performed

- The candidate reviewed and explicitly approved the principal metric, time-boundary, senior-scope, denominator, segmentation, and missing-data decisions.
- The candidate requested a more intuitive explanation when the first explanation of time coverage was unclear, then approved the corrected contract.

### Remaining risks and required verification

- Exact metric implementations have not yet been written or tested.
- Public providers and indicators have not yet been selected or verified.
- Per-source publication lag and frequency handling remain open.
- The interpretation of Streamlit as an allowed HTML experience layer should be confirmed or documented as an assumption.
- Data-quality counts found during exploratory profiling must be reproduced by the implemented pipeline and automated tests rather than trusted solely from the initial inspection.

## Stage 2: external-indicator selection

### Agent contribution

- Proposed a focused shortlist covering labour supply, labour demand, and either cost-of-living pressure or the broader economic cycle.
- Explained the tradeoffs between annual consumer-price inflation and annual GDP growth, including relevance to HR decisions, overlap with the other indicators, frequency limitations, country comparability, and the risk of causal overinterpretation.
- Recommended inflation because it adds a more distinct lens alongside unemployment and job vacancies.

### Candidate decision

The candidate selected consumer-price inflation instead of GDP growth. The approved indicator scope is therefore:

1. Eurostat monthly unemployment rate.
2. Eurostat quarterly job-vacancy rate.
3. World Bank annual consumer-price inflation.

### Rejected alternative and consequence

Annual GDP growth was considered but rejected for the first vertical slice. The main reasons were that it is a broad measure, overlaps with labour-market conditions already represented by unemployment and vacancies, and can be particularly difficult to interpret for Ireland because multinational activity can materially affect GDP.

Selecting annual inflation means that combined inflation analysis must operate at an annual comparison grain. The implementation must not repeat an annual value across quarters as if those were independent observations.

### Verification still required

- Confirm exact Eurostat dimension selections, including seasonal adjustment, age, sex, economic-activity scope, and vacancy-rate adjustment.
- Record access dates, request URLs, release cadence, publication lag, status flags, and provider/upstream-source lineage.
- Confirm that stored replay fixtures comply with the applicable dataset terms.

### API verification performed

On 2026-09-24, live read-only API queries established:

- Eurostat unemployment: all 360 expected country-month observations for 2021-2025 were returned under the corrected total-age, total-sex, percentage-of-labour-force, seasonally adjusted contract.
- Eurostat job vacancies: all 120 expected country-quarter observations were returned for the `B-S` activity scope under both adjusted and unadjusted variants. The broader `A-S` scope was incomplete and was rejected as the shared six-country scope.
- World Bank inflation: all 30 expected country-year observations for 2021-2025 were returned.

The checks also identified provider-specific country mappings and provisional vacancy observations that the pipeline must preserve.

### Agent error found and corrected during verification

The initial unemployment proposal used `Y15-74` as an age-dimension code. The live Eurostat response returned an empty age dimension because that code is not valid for `une_rt_m`. The agent inspected the dataset's actual dimensions and corrected the contract to `age=TOTAL`. The failed zero-row response will not be treated as evidence of missing country coverage.

### Candidate decision on vacancy adjustment

The agent compared four Eurostat vacancy variants: adjusted and unadjusted data for the `A-S` and `B-S` activity scopes. The candidate requested a clearer, more intuitive explanation before approving a choice. After reviewing the difference between recurring seasonal hiring and underlying labour-demand movement, the candidate approved the seasonally adjusted `B-S` series.

Consequences of the decision:

- The vacancy series remains quarterly and is never expanded into monthly observations.
- The selected scope has all 120 expected country-quarter observations for 2021-2025.
- All 33 provisional flags in the verified response must be preserved and surfaced as data-quality metadata.
- The solution must explain that seasonal adjustment is provider-supplied and that adjusted values may be revised.

## Stage 3: project foundation

### Candidate direction

The candidate approved continuing after the source contract was complete. The agreed incremental boundary was to create the maintainable project foundation without implementing retention calculations, public-data ingestion, DuckDB tables, or dashboard screens in the same step.

### Agent contribution

- Created a Python `src`-layout package and a small standard-library command-line entry point.
- Added checked-in TOML contracts for the approved countries, provider mappings, indicators, query dimensions, normalisations, and quality actions.
- Created explicit adapter, domain, pipeline, storage, and dashboard boundaries with explanations for a developer coming from .NET and Angular.
- Added a configuration-validation command and four scaffold tests.
- Created a repository-local virtual environment for verification and initialized the project as a Git repository.

### Verification and failures

- The configuration command reported six countries and three indicators as expected.
- All four scaffold tests passed after pytest was directed to a repository-local temporary directory.
- The first test run was partially blocked by denied access to pytest's default Windows temporary folder. Two tests passed and two could not start. The test configuration was changed to use `.pytest-tmp` inside the repository; the complete rerun then passed.
- A bulk dependency installation was interrupted during its final installation step. The local package and pytest were installed separately so the scaffold could be tested. The complete runtime dependency set and reproducible lock remain work for the stages that first use those libraries.

### Remaining risks

- The package boundaries are intentionally empty and have not yet demonstrated real ingestion or metric behaviour.
- Broad dependency constraints exist, but an exact verified lock has not yet been generated.
- Streamlit remains an optional dependency until the dashboard stage and the HTML-option interpretation remains documented as an assumption requiring confirmation.

## Stage 4: supplied-workforce ingestion and quality

### Candidate direction

The candidate approved continuing with the next incremental stage after reviewing the project foundation. The scope remained limited to supplied-file integrity, normalisation, analytical eligibility, hard quarantine, and quality evidence; retention calculations and external ingestion were deliberately excluded.

### Agent contribution

- Copied the four supplied synthetic artifacts into `data/input` without modifying their content.
- Implemented SHA-256, byte-count, and logical-row-count checks against the supplied manifest.
- Implemented deterministic duplicate removal, approved alias normalisation, ISO-date validation, chronology validation, unknown-classification preservation, and visible exclusion reasons.
- Added a `prepare-workforce` CLI command and deterministic CSV/JSON outputs.
- Added unit, integrity, and end-to-end tests, plus human-readable data-quality evidence.

### Verification performed

- All three manifest-declared CSV files matched their hashes, sizes, and row counts.
- The complete test suite passed: 12 tests.
- The real preparation command reconciled 2,407 source rows to 2,381 analytical rows, 14 metric-ineligible rows, 5 hard-quarantined rows, and 7 removed exact duplicates.
- The implemented issue counts reproduced the exploratory profile, including eight country aliases, ten career-level aliases, thirteen missing termination types, and fourteen unknown regretted-exit classifications on termination records.

### Important implementation decisions

- Source row numbers begin at 2 so they correspond to physical CSV lines after the header.
- Exact duplicates retain the first physical source row.
- A row can have multiple issue records, so issue count is not the same as excluded-row count.
- Missing termination type and missing regretted classification remain warnings when the date information is otherwise usable.
- Generated results are deterministic and contain no run timestamp. Retrieval timestamps will be required for later external API ingestion, where freshness is part of the source contract.

### Remaining risks

- The supplied data has one row per employee after exact deduplication. A later source version with conflicting non-identical records for an employee ID will hard-quarantine the conflict and fail validation; the pipeline never chooses one silently.
- Generated CSV files use empty fields to preserve unknown classifications. Later DuckDB tables must use explicit null types and retain the warning codes.
- Retention metric tests have not yet been written because metric implementation remains the next separate increment.

### Candidate correction to exclusion terminology

The candidate compared the Stage 4 description with the previously approved quality-policy table and challenged the statement that all 19 excluded rows were “quarantined.” The agent confirmed that this wording and the shared quarantine output were too broad.

The candidate approved this correction:

- Nine missing-country rows are `METRIC_INELIGIBLE` for the approved country-level analysis, not hard-quarantined.
- Five missing-hire-date rows are `METRIC_INELIGIBLE` for time-based metrics and headcount and therefore cannot enter any of the three current objectives; they are not hard-quarantined.
- Five termination-before-hire rows are `HARD_QUARANTINE` because their chronology is impossible.
- All 19 remain outside the analytical workforce but are preserved in one excluded-record evidence file with an explicit classification and reason code.

The candidate further required the original data-quality decisions to use clear and unambiguous phrasing everywhere in the project. The implementation, configuration, CLI output, filenames, tests, requirements, README, and quality evidence were updated together to prevent terminology drift.

## First retention objective: six-month new-hire retention

### Candidate-approved rules used

- Quarterly country-level cohort reporting.
- Calendar-month anniversaries.
- A termination on the anniversary counts as retained through that anniversary.
- Business unit is the primary workforce segment.
- Metric-ineligible and hard-quarantined records remain outside the analytical workforce.
- Workforce objective coverage starts on 2021-01-01; earlier employment history is not treated as a pre-objective new-hire cohort.

### Agent contribution

- Implemented the `NEW_HIRE_6M` formula as a pure domain function.
- Produced separate country-total and business-unit aggregation levels.
- Preserved immature cohorts as `NOT_YET_MEASURABLE` instead of treating them as success or failure.
- Added a re-runnable command that performs workforce quality preparation before calculating the metric.
- Added hand-checkable boundary tests and end-to-end reconciliation tests.

### Verification performed

- All 22 tests passed after this increment.
- The real run reconciled 1,969 in-scope hires into 1,808 eligible hires and 161 not-yet-measurable hires.
- The 1,808 eligible hires reconciled to 1,576 retained and 232 exited before the anniversary.
- The resulting overall weighted rate was approximately 87.17% against an 86% target.

### Interpretation boundary

The overall result is not yet promoted as a final business finding. Country-quarter sample sizes vary, the remaining objectives are not implemented, and no external context or association analysis exists yet.

## Candidate verification: Windows test permissions

The candidate ran the test suite from their normal Windows account and reported that only 17 tests passed while five ended with `PermissionError: [WinError 5]`. This manual verification exposed a cross-account problem: persistent pytest cache and temporary folders created by the Codex sandbox account were not accessible to the candidate's account.

The agent changed the test configuration to disable pytest's persistent cache and added a self-cleaning, uniquely named temporary-directory fixture. The inaccessible generated `.pytest_cache` and `.pytest-tmp` folders were removed; they contained no source data or project work. After the change, all 22 tests passed and neither shared folder was recreated.

## Second retention objective: twelve-month senior-hire retention

### Candidate-approved rules used

- Quarterly country-level cohort reporting.
- Calendar-month anniversaries.
- A termination on the anniversary counts as retained through that anniversary.
- `Senior Leader` and the normalised `Sr Mgmt` alias count as senior; `Manager` does not.
- Business unit is the primary workforce segment.
- Workforce objective coverage starts on 2021-01-01; earlier hires are not treated as pre-objective senior-hire cohorts.

### Agent contribution

- Refactored the shared hire-cohort calculation into one internal rule so the six- and twelve-month definitions cannot drift apart silently.
- Added the explicitly named twelve-month senior-hire domain function, pipeline command, auditable CSV and JSON outputs, boundary tests, and methodology documentation.
- Kept this increment limited to the second retention objective; regretted turnover, external ingestion, DuckDB, and dashboard work remain separate.

### Verification performed

- All 28 tests passed, including the unchanged six-month objective tests.
- The supplied data reconciled 314 in-scope senior hires into 266 eligible hires and 48 not-yet-measurable hires.
- The 266 eligible hires reconciled to 209 retained and 57 exited before the anniversary.
- The resulting overall weighted rate was approximately 78.57% against a 90% target.

The candidate's normal Windows account owns the existing generated output files, so the Codex sandbox correctly could not overwrite them. The real-data calculation was therefore verified in a separate temporary folder, which was removed after verification. The candidate can generate the normal output files under their own account with the documented command.

### Interpretation boundary

The overall result is below the supplied objective, but it is not yet promoted as a final business finding. Country-quarter sample sizes vary, the regretted-turnover objective is unfinished, and no external context or association analysis exists yet.

## Third retention objective: trailing twelve-month regretted turnover

### Candidate clarification and approval

The candidate asked for a clearer explanation of two proposed rules: keeping country totals separate from business-unit detail, and treating the one supplied business-unit value per employee as constant through history. The agent explained that totals already contain their segments and would be double-counted if mixed, and that no dated transfer history exists. The candidate approved the complete turnover contract.

The approved implementation rules are:

- Quarter-end reporting from 2021 Q1 through 2025 Q4.
- An inclusive trailing-twelve-month termination window.
- The arithmetic mean of exactly twelve month-end active headcounts.
- A termination on month end counts in that month's headcount because it is the employee's last employed day.
- Only explicit `true` values enter the regretted-exit numerator; blank classifications remain unknown and are reported separately.
- Country totals and business-unit detail are separate aggregation levels.
- Pre-2021 employment may support early headcounts and turnover windows.
- The supplied business unit is treated as constant because no transfer history exists; this is documented as a limitation.

### Agent contribution

- Implemented the pure turnover calculation, re-runnable pipeline command, auditable CSV and JSON outputs, tests, and methodology documentation.
- Preserved true, false, and unknown exit classifications as separate output counts.
- Avoided creating a misleading overall 2021-2025 rate because overlapping rolling windows would repeatedly count the same exits.

### Verification performed

- All 34 tests passed after this increment.
- The supplied data produced 20 reporting quarters, 120 country-quarter rows, and 480 business-unit rows.
- Across the full period, 108 country-quarter results met the target and 12 were above it.
- All six latest-quarter country results met the target. Ireland and Poland each retained one visibly unknown regretted-exit classification in that window.

As with the prior metric, Codex used and then removed a separate temporary verification folder rather than overwrite generated files owned by the candidate's Windows account.

### Interpretation boundary

These results are descriptive workforce outcomes. No causal claim will be made, rolling-quarter results will not be summed across time, and the effect of unobserved business-unit transfers remains an explicit limitation.

## First external indicator: Eurostat unemployment

### Candidate approval

The agent explained how 360 monthly country observations become 120 quarterly means, why all three months are required, how Eurostat `EL` maps to canonical `GR`, and how publication lag and revisions affect interpretation. The candidate approved the following contract:

- retain both native monthly observations and derived quarterly means;
- require all three monthly values for a complete quarterly rate;
- record the typical approximately 31-day publication lag;
- describe the use of latest retrieved values as retrospective current-vintage analysis;
- preserve the raw response, request URL, retrieval time, checksum, provider update time, and observation statuses; and
- never pretend to reconstruct the value that was originally available during a historical quarter.

### Agent contribution

- Implemented a small `httpx` Eurostat adapter, defensive JSON-stat parsing, explicit country mapping, pure quarterly aggregation, auditable file outputs, CLI command, offline tests, and methodology documentation.
- Kept the increment limited to unemployment; job vacancies, inflation, DuckDB, joins, and dashboard work remain separate.
- Automated tests use a small synthetic JSON-stat response and do not depend on live internet availability.

### Verification performed

- All 39 tests passed.
- A live official-API run returned all 360 expected monthly observations with no missing values and produced all 120 expected complete quarters.
- Eurostat reported a dataset update of 2026-09-22T11:00:00+0200.
- The verification response, retrieved on 2026-09-25, had SHA-256 checksum `d884e560c77f932780e629aea2539afed40c3acfeead1dab8f2ec265d265e79a`.

The live run used an isolated temporary folder because generated project files are owned by the candidate's Windows account. Both the failed restricted-network folder and successful verification folder were removed after verification. The candidate's own command will write the retained evidence files under their account.

### Interpretation boundary

Unemployment is contextual evidence, not proof of a causal effect on retention. Same-period values may have been published after the period ended, so the eventual combined analysis must remain explicitly retrospective.

## Second external indicator: Eurostat job vacancies

### Candidate clarification and approval

The agent proposed preserving provisional values, recording 50-day flash and 78-day fuller-result publication timing, attaching Italy's reduced-coverage warning, and locking the historical query to NACE Rev. 2 rather than silently switching to NACE Rev. 2.1. The candidate requested a more intuitive explanation of publication delay and dataset-version safety.

The agent used a 2024 Q1 release timeline to distinguish the period described from the later publication dates and compared the classification change to a versioned API whose values can retain the same shape while changing business meaning. The candidate then approved all recommendations.

### Agent contribution

- Generalised the existing Eurostat JSON-stat parsing core while retaining indicator-specific public functions and schemas.
- Implemented the approved native-quarterly ingestion, provisional flag preservation, Italy coverage warning, dataset-version guard, raw evidence, CLI command, offline tests, and documentation.
- Kept the increment limited to job vacancies; inflation, DuckDB, combined analysis, and dashboard work remain separate.

### Verification performed

- All 43 tests passed, including the existing unemployment regression tests.
- A live official-API run returned all 120 expected quarterly values with no missing observations.
- The current response contained 33 provisional values and 20 Italy rows with the explicit coverage warning.
- Eurostat reported a dataset update of 2026-03-20T23:00:00+0100.
- The verification response had SHA-256 checksum `f3c5de9b3a94d6d79f3c962f72be98201f76fa3e6a31976e87bb5ee2484b33a1`.

The live run used an isolated temporary folder so it did not overwrite candidate-owned generated files. That verification folder was removed after the run; the candidate's own command creates the retained evidence.

### Interpretation boundary

Job vacancies are contextual labour-demand evidence, not proof that vacancies caused employee departures. Provisional status, publication lag, revisions, and Italy's reduced coverage must remain visible in later comparisons.

## Third external indicator: World Bank consumer-price inflation

### Candidate approval

The agent explained the annual indicator's meaning, why one annual value must not become four artificial quarterly observations, the lack of a defensible fixed publication-lag number, current-vintage revision treatment, visible missing country-years, provider country mapping, and CC BY 4.0 attribution. The candidate approved all recommendations.

### Agent contribution

- Implemented a dedicated World Bank Indicators API adapter, explicit six-country mapping, complete expected country/year grid, annual-frequency preservation, raw evidence, lineage, attribution, CLI command, offline tests, and methodology documentation.
- Missing observations remain null and visible; no interpolation, carry-forward, or quarterly expansion is performed.
- Kept this increment limited to inflation ingestion. DuckDB, combined analysis, and dashboard work remain separate.

### Verification performed

- All 48 tests passed.
- A live official-API run produced all 30 expected country-year rows with all 30 values available and none missing.
- The API identified source ID `2`, World Development Indicators, and reported a provider last-update date of 2026-07-13.
- The verification response had SHA-256 checksum `1eb8a64d373dbe032b455a15cfc0a75cdd48bb801859691224180d7d7e3c4eab`.

The live run used an isolated temporary folder so it did not overwrite candidate-owned generated files. That verification folder was removed after the run; the candidate's command creates the retained evidence.

### Interpretation boundary

Inflation is annual cost-of-living context, not a quarterly measurement and not proof of a causal effect on retention. The exact annual workforce aggregation for later comparison remains a separate candidate-reviewed decision.

## Local DuckDB storage

### Candidate approval

The agent proposed one local DuckDB file with three SQL Server-like schemas: `canonical` for cleaned source-grain data, `analytics` for calculated results, and `audit` for quality and load evidence. Raw JSON, original inputs, and JSON summaries remain files. The candidate approved this structure and an atomic rebuild that preserves the previous database if any new load fails.

### Agent contribution

- Implemented a fixed ten-file table contract, missing-input validation, temporary database construction, row-count reconciliation, `audit.table_loads`, atomic replacement, CLI command, failure-preservation tests, and storage documentation.
- Avoided indexes, a server process, duplicated raw JSON, migration infrastructure, and combined-analysis views that are unnecessary at this stage.

### Verification performed

- All 51 tests passed.
- The real `data/output/asteria.duckdb` was created successfully with 11 tables: ten file-backed tables plus `audit.table_loads`.
- Read-only verification reconciled 2,381 workforce rows, 360 monthly unemployment rows, 120 quarterly unemployment rows, 120 vacancy rows, 30 inflation rows, 592 new-hire result rows, 331 senior-hire result rows, 600 turnover result rows, 71 quality-issue rows, and 19 excluded-record rows.

### Remaining boundary

The database currently stores prepared results but does not yet join workforce outcomes to external indicators or calculate associations. Those temporal-alignment decisions remain candidate-reviewed work.

## Temporal alignment and combined context

### Candidate clarification and approval

The agent initially proposed quarterly and annual alignment, count-weighted annual retention, Q4 calendar-year turnover, and visible small-group warnings. The candidate stated that the explanation was not understandable. The agent then restated the design using four concrete rules: compare like periods, keep inflation annual, add people before calculating annual retention, and warn rather than remove small groups. The candidate approved the simplified contract.

This correction materially influenced the communication and implementation record: the project documents now explain alignment with concrete time windows and people counts rather than relying on statistical terminology alone.

### Approved rules implemented

- Hire-cohort retention uses unemployment and vacancies from the hire quarter.
- Trailing-twelve-month turnover uses twelve unemployment months and four vacancy quarters covering the same window.
- Annual retention sums numerators and denominators before calculating the rate.
- Annual turnover uses Q4 because its trailing window equals the calendar year.
- Annual inflation remains annual.
- Retention denominators of 1-9 receive `SMALL_SAMPLE`; turnover average headcount greater than 0 but below 20 receives `LOW_AVERAGE_HEADCOUNT`.
- Warnings never suppress or change a result.

### Agent contribution

- Added warnings to the original metric outputs.
- Implemented pure quarterly and annual alignment functions, completeness checks, current-vintage warnings, output pipelines, CLI command, tests, documentation, and two DuckDB analytical tables.
- Refused partial trailing-window averages when 2020 external history was unavailable.

### Verification performed

- All 55 tests passed before real-output generation.
- The real run produced 1,523 quarterly rows and 436 annual rows.
- The quarterly output contains 774 small-group or low-headcount warnings; the annual output contains 126.
- Exactly 18 country-quarters have incomplete trailing external context: six countries across 2021 Q1-Q3. The first complete trailing period is 2021 Q4.
- All annual rows found their approved inflation country/year match.
- DuckDB was atomically rebuilt with 13 total tables, including the two combined context tables; their verified row counts are 1,523 and 436.

### Interpretation boundary

The combined files provide aligned descriptive context. They do not yet calculate correlations, select final findings, or imply that economic indicators caused workforce outcomes.

## Candidate correction: extend Eurostat support history to 2020

### Candidate contribution

After reviewing the incomplete 2021 Q1-Q3 turnover context, the candidate asked why unemployment and vacancies had not been downloaded from 2020 and whether doing so was recommended. This exposed a planning gap: the implementation had followed the approved 2021-2025 external reporting period literally without revisiting the extra history required by a trailing-twelve-month comparison.

The agent acknowledged the oversight and verified the official 2020 Eurostat coverage before recommending the correction. The candidate approved extending unemployment and vacancies to 2020 and explicitly required this contribution to be recorded in `AI_USAGE.md`.

### Approved correction

- Workforce objectives and reporting remain 2021-2025.
- Unemployment ingestion now covers 2020-01 through 2025-12.
- Job-vacancy ingestion now covers 2020-Q1 through 2025-Q4.
- Inflation remains 2021-2025 because it is not used in a rolling lookback.
- The 2020 Eurostat observations are support history only and do not create pre-2021 workforce results.
- The exceptional COVID-19 context of 2020 must be considered when interpreting early 2021 results.

### Implementation and verification

- Added separate indicator-level ingestion starts so workforce reporting dates and external support history are not conflated.
- Refreshed unemployment to 432 complete monthly observations and 144 complete quarterly means, with no missing values.
- Refreshed job vacancies to 144 complete quarterly observations, with 37 provisional values and no missing values.
- Rebuilt both combined outputs and DuckDB.
- Incomplete trailing external country-quarters fell from 18 to 0; full aligned turnover context now begins at 2021 Q1.
- All 55 tests passed after the correction.

This correction is directly attributable to the candidate's supervision and challenge of the initial coverage decision.

## Country-total association analysis

### Candidate approval

The agent proposed a deliberately small association stage: Spearman rank correlation, nine separate objective/indicator comparisons, country totals only, complete pairs only, and explicit interpretation limits. The candidate asked for a clearer explanation of the difference between same-quarter unemployment and trailing unemployment before approving the recommendations. That clarification confirmed that the underlying unemployment series is the same, while its averaging window changes to match the workforce metric's window.

### Approved implementation

- Six quarterly comparisons cover each workforce objective against unemployment and job vacancies.
- Three annual comparisons cover each workforce objective against consumer-price inflation.
- Hire-cohort comparisons use same-hire-quarter external conditions; turnover comparisons use matching trailing-twelve-month conditions.
- Only country-total rows enter correlation. Business-unit rows remain available for detail but do not repeat a single national indicator value in the statistical sample.
- The exact Spearman coefficient, direction, paired observation count, country count, period, warned-row count, and calculation status are reported.
- No arbitrary strength labels or causal claims are added.
- Results retain warnings for repeated countries over time, current-vintage external data, and association-not-causation.

### Agent contribution

The agent implemented the pure-pandas calculation, failure-safe pipeline output, command-line entry point, offline tests, DuckDB table, and plain-language method documentation. No additional statistical dependency, predictive model, significance-test framework, or business-unit pseudoreplication was introduced.

### Verification performed

- All 60 automated tests passed.
- All nine approved comparisons were calculated across all six countries.
- The usable-pair counts are 108 for each new-hire quarterly comparison, 90 for each senior-hire quarterly comparison, 120 for each turnover quarterly comparison, and 30, 24, and 30 for the three annual inflation comparisons.
- All 90 senior-hire quarterly pairs carry the approved small-sample warning, so those coefficients require particular caution.
- DuckDB was atomically rebuilt with fourteen total tables: thirteen file-backed tables plus `audit.table_loads`. The new `analytics.association_results` table contains nine rows, and `audit.table_loads` contains thirteen reconciled load rows.

### Remaining boundary

The coefficients are reproducible calculation outputs, but the candidate has not yet selected or approved the final business findings and narrative. Dashboard work also remains separate.

## Approved findings and narrative

### Candidate contribution and approval

The agent presented four candidate findings in plain language and explicitly separated measured facts from interpretation. The candidate approved all four findings:

1. Six-month new-hire retention generally met its objective, with visible exceptions and a partial-period warning for 2025.
2. Twelve-month senior-hire retention is the clearest workforce concern, subject to strong small-cohort caution and no measurable 2025 result yet.
3. Regretted turnover remained within the annual objective, while the 2025 increase and twelve country-quarter exceptions warrant monitoring.
4. The selected indicators provide no clear overall economic explanation; the largest observed coefficient remains non-causal and near-zero inflation results are retained as a useful non-finding.

The candidate's approval determines which evidence will be presented as the central dashboard narrative. The agent did not independently promote additional coefficients or segment differences into business conclusions.

### Agent contribution

The agent queried the validated DuckDB outputs, reconciled every proposed number with the underlying numerators and denominators, explained partial-period and small-sample constraints, and recorded the approved narrative in `docs/findings.md`. No predictive, causal, or significance claim was introduced.

### Remaining boundary

The findings are approved, but their visual presentation and interaction design remain a separate candidate-reviewed dashboard stage.

## Interactive Streamlit dashboard

### Candidate approval

The agent proposed one focused local dashboard with country, year, objective, and business-unit filters; workforce metrics and trends; economic relationship views; the four approved findings; and a trust area covering quality, freshness, sources, and methodology. The agent also proposed that economic relationships remain country-level even when business-unit detail is explored because the selected external indicators are national. The candidate approved this design.

### Agent contribution

- Implemented a read-only DuckDB dashboard data boundary separate from the Streamlit interface.
- Added filter-aware workforce summaries that recalculate rates from approved numerators and denominators rather than averaging percentages.
- Added objective trends, target lines, business-unit comparisons, and current-filter relationship views using the same Spearman calculation as the analytical pipeline.
- Added sample counts, warnings, explicit non-causation language, retrieval timestamps, quality and exclusion counts, source attribution, methodology, and known limitations.
- Added graceful missing/incomplete-database handling with a recovery instruction instead of exposing a traceback.
- Added automated data-boundary and UI recovery tests.

### Verification performed

- The full suite passed: 65 tests.
- A Streamlit smoke test against the real DuckDB database rendered all three tabs with no exceptions or errors.
- The default page reconciled the approved 87.2% new-hire rate, 86.0% target, 108 paired observations, 71 quality-evidence rows, 19 excluded rows, and 13 file-backed database loads.
- The agent visually inspected the workforce, economic-context, and trust/methodology tabs in the rendered local browser page. Labels, controls, charts, warnings, attribution, and data tables were visible without layout errors.
- Changing the objective filter to senior-hire retention correctly produced 78.6%, a 90.0% objective, `MISSED`, 90 economic pairs, and the expected 90-row small-sample warning.

### Remaining boundary

A representative screenshot or export, one-command core orchestration, production architecture view, and final presentation artifact remain separate increments.

## One-command core workflow

### Candidate approval

The candidate approved one Python CLI command for the complete online workflow and an `--offline` mode that reuses previously downloaded external data. The dashboard remains a separate long-running command.

### Agent contribution

- Implemented ordered orchestration across configuration, input integrity, one shared workforce preparation, three objectives, external context, combined analysis, associations, and an atomic DuckDB rebuild.
- Kept every individual stage command available for focused troubleshooting.
- Implemented offline validation for required columns, duplicate country-period keys, and complete configured external-data grids.
- Rebuilds derived quarterly unemployment from cached monthly observations in offline mode.
- Added stage progress, named failures, non-zero failure exit codes, and `core_run_summary.json` success/failure evidence.
- Ensured DuckDB is the final stage so an earlier failure does not replace the previous working database.

### Failure found during human-scale verification

The first real offline run exposed a CSV round-trip difference: blank Eurostat observation statuses were read back as null values rather than in-memory empty strings. The shared unemployment aggregation was corrected to ignore both representations, and a regression test was added. The failed run stopped during cached-data validation and did not rebuild DuckDB.

### Verification performed

- The real offline command completed all ten offline stages and rebuilt DuckDB successfully.
- Automated tests cover online ordering, offline no-download behaviour, named failure evidence, database-last ordering, CLI success/failure reporting, and the blank-status CSV round trip.

### Remaining boundary

The individual live API adapters were already verified separately. A default online core run performs a fresh external-data retrieval and may legitimately produce a newer current data vintage.

## Production architecture blueprint

### Candidate approval

The candidate approved a documentation-only production mapping from the working local project to Azure Data Factory orchestration, lakehouse storage, Databricks processing, and Power BI consumption. No cloud deployment or additional local runtime technology was authorised or introduced.

### Agent contribution

- Added one production flow diagram and a direct local-to-production mapping.
- Explained Raw/Bronze, Cleaned/Silver, and Reporting/Gold as preparation levels rather than separate products.
- Covered every assessment topic: secrets, scheduling, failure handling, observability, storage and replay, role-based access, and promotion through separate development, test, and production environments.
- Explicitly retained business rules in tested processing code rather than placing them in orchestration or dashboard tools.
- Documented that Databricks is a scale destination, not a requirement for the supplied dataset, and that the architecture is a blueprint rather than deployed paid infrastructure.

## Network-independent replay evidence

### Candidate approval

The candidate approved retaining one small public response for each selected external indicator and using those responses as an offline fallback when prepared external files are absent. Committing all generated CSV and DuckDB outputs was rejected because it would duplicate derived answers and provide weaker evidence that source parsing works.

### Agent contribution

- Added reviewed Eurostat unemployment, Eurostat job-vacancy, and World Bank inflation replay responses, totalling approximately 23 KB.
- Added a manifest containing provider, request URL, historical retrieval time, original payload checksum, and World Bank attribution and licence.
- Added checksum verification before parsing; a modified fixture fails rather than silently entering analysis.
- Preserved the original retrieval vintage and clearly distinguished replay from a new download.
- Extended offline mode to prefer validated local canonical data and fall back to replay only when those prepared files are missing.
- Sent replay payloads through the same provider adapters used by online ingestion.

### Verification performed

- A fresh-directory test rebuilt all 432 unemployment months, 144 job-vacancy quarters, and 30 inflation country-years solely from the replay responses.
- A complete offline workflow test starts with no generated external files, builds every analytical output, and creates a new DuckDB database without network access.

## Final 15-minute presentation

### Candidate approval and direction

The candidate approved a simple Markdown presentation and explicitly required it to cover the assessment's full 15-minute structure. The candidate's earlier approvals determine the metric contract, data-quality treatments, source choices, temporal alignment, findings, dashboard design, architecture boundaries, and AI-accountability examples presented in the deck.

### Agent contribution

- Translated the assessment's exact agenda into four timed sections: 3 minutes for problem refinement and scope, 5 minutes for architecture, lineage, and reliability, 4 minutes for the dashboard and key findings, and 3 minutes for tradeoffs, AI usage, and next steps.
- Created a concise Markdown presentation using only verified project outputs and candidate-approved interpretations.
- Added a separate plain-English speaking guide with an exact live-demo route, offline preparation commands, a failure fallback, and short answers to likely technical and analytical questions.
- Included the candidate's 2020 support-history correction and the reviewed-fixture decision as concrete evidence of supervision, challenge, and material change rather than presenting AI use as unattended generation.

### Ownership boundary

The presentation does not introduce new business findings or causal claims. The candidate remains responsible for rehearsing the timing, explaining every claim, navigating the implementation during questions, and changing the reasoning if challenged during the interview.

### Verification performed

- All 73 automated tests that existed at the presentation stage passed after the presentation files and documentation links were added.
- The speaking allocations reconcile exactly to 15 minutes and preserve the assessment's required 3/5/4/3-minute split.
- Presentation claims were checked against the approved findings, architecture, source, quality, and workflow documentation.

## Bounded public-API retries

### Candidate approval

During the final readiness review, the agent identified that public-source requests had timeouts, status validation, clear errors, offline replay, and safe pipeline failure behaviour, but no bounded retry for short-lived provider problems and no focused HTTP-failure tests. After a plain-language explanation of the difference between online retries and offline replay, the candidate approved a small retry increment.

### Approved implementation

- Retry transport failures, HTTP 429, and HTTP 500, 502, 503, and 504 because they may be temporary.
- Make at most three attempts with one- and two-second waits.
- Fail immediately for other HTTP client errors because repeating a permanently invalid request does not help.
- Preserve provider-specific final error messages and the existing database-last safety boundary.
- Test with fake HTTP responses so the suite is fast and does not depend on live providers.

### Agent contribution and verification

The agent introduced one shared HTTP helper used by both Eurostat and World Bank adapters, added focused success-after-retry, repeated-timeout, permanent-error, and rate-limit tests, and documented the behaviour in the core workflow and README. No infinite retry, third-party retry dependency, or automatic switch to stale data was introduced.

- All four focused retry tests passed using fake HTTP responses and no live network access.
- The complete suite passed with 77 tests after the change.

## Exact dependency lock

### Candidate approval

During submission-readiness review, the agent explained the difference between broad dependency compatibility ranges in `pyproject.toml` and an exact tested lock using the candidate's familiar `package.json`/`package-lock.json` and `.csproj`/`packages.lock.json` comparisons. The candidate approved adding a simple Python lock without introducing another package-management technology.

### Agent contribution and verification

- Inspected the active project environment and confirmed that all installed packages belong to the direct or transitive application, dashboard, or test dependency graph.
- Added `requirements.lock` with the exact direct and transitive versions verified on Python 3.12.14.
- Updated Windows setup to install the lock first and the local package second with `--no-deps`, so broad `pyproject.toml` ranges do not replace locked versions.
- Kept `pyproject.toml` as the readable package and compatibility contract rather than duplicating exact pins there.
- Compared the lock with the active environment and confirmed an exact package/version match.
- A no-index installation dry run found every locked requirement satisfied, and `pip check` reported no broken requirements.
- The complete suite still passed with 77 tests after the setup and lock changes.

## Final documentation consolidation

### Candidate direction

The candidate approved replacing outdated development-stage wording, adding a consolidated README limitations section, identifying the AI tool and model, and using explicit virtual-environment dashboard commands. The candidate then supplied the final effort statement: completed incrementally over several days, with approximately 20 hours of active work.

### Agent contribution and verification

- Reframed the README around the final problem, scope, implemented solution, architecture, commands, and known limitations.
- Replaced stale “not yet final” metric wording with the candidate-approved findings and converted the requirements document's open decisions into their implemented resolutions.
- Added the Codex and GPT-5 disclosure while preserving the chronological AI record instead of rewriting historical stage entries.
- Added a resolution summary showing which earlier risks were closed and which submission-packaging tasks remain.
- Replaced dashboard and development commands with explicit `.venv` Python commands that do not depend on successful shell activation.
- Searched the final documentation and found no remaining stale unfinished wording outside the intentionally chronological AI history, and no remaining fragile bare dashboard or project commands.

## Representative generated evidence

### Candidate direction and contribution

The candidate approved a small reviewer-facing evidence package rather than committing every generated output or the binary DuckDB database. The candidate captured and supplied seven dashboard screenshots covering all three workforce objectives, all three economic-context objective views, and one shared Trust and methodology view.

### Agent contribution

- Added a dedicated `evidence` folder with an assessment-to-artifact map, selection rules, provenance, and deliberate exclusions.
- Created an 18-row deterministic curated-workforce sample using the first three stable-sorted records from each of the six canonical countries.
- Copied the calculated workforce-quality and combined-coverage summaries without changing their values.
- Added a three-row objective summary with auditable counts, denominators, rates, targets, statuses, periods, and caveats.
- Included all nine approved association results without sampling.
- Copied the seven candidate-supplied screenshots byte-for-byte while correcting the accidental `.png.png` filenames to `.png` in the repository.
- Added concise source attribution distinguishing the current online evidence retrieval from the preserved offline replay vintage.

### Verification performed

- The curated sample contains exactly three records for each of BG, GR, IE, IT, PL, and RO.
- The objective summary reconciles to 1,576/1,808 new hires, 209/266 senior hires, and 80/1,605.0833 for the 2025 Q4 turnover window.
- The complete association evidence contains exactly nine calculated comparisons.
- The copied reports match their generated source files byte-for-byte.
- All seven screenshot copies match the candidate-supplied files byte-for-byte and have readable 1,366-pixel widths.

## Fresh-clone Windows portability correction

### Candidate direction and contribution

After publishing the repository, the candidate performed the planned clean-clone rehearsal on Windows. The candidate reported that the offline workflow rejected the unemployment replay fixture because its checksum no longer matched, then approved a repository-level portability correction and a simpler quick-start environment command.

### Agent contribution and verification

- Compared the original and cloned fixture bytes and identified that Git's Windows `core.autocrlf=true` setting had changed the final LF byte to CRLF during checkout.
- Added a narrow `.gitattributes` rule that keeps all checksum-protected replay JSON files at LF on every operating system without changing their content or weakening checksum validation.
- Simplified the first quick-start command from a Windows-launcher-specific Python 3.11 invocation to `python -m venv .venv`; the documented prerequisite remains Python 3.11 or newer.
- Re-ran the complete offline workflow successfully through all ten stages, including replay validation and DuckDB rebuilding.
- Re-ran the complete automated suite: 77 tests passed.
