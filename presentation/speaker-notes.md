# 15-minute speaking guide

This guide follows the assessment's required timing exactly. The wording is a guide, not a script you must memorise. Speak slowly, use your own words, and stop when each section's time expires.

## Timing at a glance

| Assessment section | Slides | Time |
| --- | --- | ---: |
| Problem refinement and scope | 1–2 | 3:00 |
| Architecture, lineage, and reliability | 3–6 | 5:00 |
| Dashboard and key findings | 7–9 | 4:00 |
| Tradeoffs, AI usage, and next steps | 10–11 | 3:00 |
| **Total** |  | **15:00** |

The Questions slide is not part of the first 15 minutes. Leave it visible for the following 15-minute discussion.

Open the title slide before the interview begins. Start the 15-minute clock when you move to content slide 1, “Problem refinement and scope.” The slide numbers below refer to the 11 content slides and do not count the opening title or closing Questions slide.

## Before the interview

From the repository root, prepare the product without relying on internet access:

```cmd
.venv\Scripts\python.exe -m asteria_retention run --offline
```

Then start the dashboard in a second terminal:

```cmd
.venv\Scripts\python.exe -m streamlit run dashboard\app.py
```

Open the dashboard before the interview. Keep these files ready as backups:

- `docs/requirements.md`
- `docs/data-quality.md`
- `docs/findings.md`
- `docs/architecture.md`
- `AI_USAGE.md`
- `data/output/core_run_summary.json`

If the dashboard cannot start, continue with the result tables in the presentation and explain that offline replay plus the automated tests verify the same prepared outputs.

## 1. Problem refinement and scope, 3 minutes

### Slide 1, about 1 minute 20 seconds

Suggested explanation:

“The broad topic is retention and the economy, but this data cannot prove that economic conditions cause employee outcomes. I narrowed the work to three defensible questions: whether the objectives were met, where results need attention, and whether selected public indicators show a useful descriptive relationship.”

Point out the time boundary:

- Workforce objectives cover 2021–2025.
- Unemployment and vacancy data start in 2020 only because early-2021 turnover needs a complete previous-twelve-month economic window.
- Inflation remains annual because the source is annual.

### Slide 2, about 1 minute 40 seconds

Explain “metric contract” in plain language:

“Before writing calculations, I decided exactly what each measure means, who belongs in it, and how edge cases are treated. This prevents two developers from producing different answers from the same data.”

Do not read every bullet. Emphasise three decisions:

1. Calendar-month anniversaries avoid inventing a day-level rule the assessment did not provide.
2. The turnover denominator uses 12 month-end headcounts, so the numerator and denominator cover the same year.
3. Unknown values are not guessed; exclusions have visible reasons.

Transition: “With the meaning fixed, I could keep the implementation simple and separated.”

## 2. Architecture, lineage, and reliability, 5 minutes

### Slide 3, about 1 minute 20 seconds

Move left to right through the diagram. Relate it to your background:

“Adapters are like infrastructure clients in .NET. Domain modules contain business meaning. Pipeline services are the application layer. DuckDB is local persistence. Streamlit is a thin UI, similar to keeping business logic out of Angular components.”

Main point: a source-format change should not silently change a metric formula, and a UI change should not change the stored answer.

### Slide 4, about 1 minute 10 seconds

Explain source fitness, not just source popularity:

- Eurostat supplies comparable European unemployment and vacancy series for the six countries.
- The World Bank supplies annual consumer-price inflation.
- Source limitations remain visible: publication delay, revisions, provisional values, and different frequencies.

Explain lineage simply:

“Lineage means I can trace a dashboard number backward through the analytical table and cleaned data to the source and its retrieval metadata.”

### Slide 5, about 1 minute 50 seconds

Start with the quality distinction:

“A bad row is not always bad in the same way. A missing country prevents country analysis, while a missing hire date prevents time-based metrics. I preserve the record and reason, but only allow it into calculations it can genuinely support.”

Then explain the failure design:

- Online mode refreshes public sources.
- Offline mode allows a reliable demonstration without network access.
- Reviewed replay fixtures test the real source parsers rather than bypassing them.
- Checksums detect changed fixtures.
- The database is replaced only after all required stages succeed.

Mention the current test count from your final test run. Do not rely on a memorised number if it changes; show the terminal result if asked.

### Slide 6, about 40 seconds

Keep this short:

“The supplied data does not need enterprise cloud tools. This diagram shows how the same responsibilities map to the requested production stack: ADF coordinates, the lakehouse preserves stages, Databricks runs tested transformations at scale, and Power BI consumes approved reporting data. Security and operations are added around that flow.”

Transition: “Now I will show what the user actually sees.”

## 3. Dashboard and key findings, 4 minutes

### Slide 7 and live dashboard, about 1 minute 30 seconds

Use this exact demonstration path to avoid losing time:

1. Show the default new-hire result and target.
2. Select senior-hire retention to show 78.6%, the 90% objective, and the warning.
3. Change one business-unit filter to demonstrate detail.
4. Open Economic context and point to paired observations and non-causation text.
5. Open Trust and methodology and point to exclusions, sources, and retrieval evidence.

Do not explore every filter. The aim is to prove usability, evidence, and trust.

### Slide 8, about 1 minute 30 seconds

Lead with the hierarchy:

1. Senior-hire retention is the clearest concern: 78.6% versus 90%.
2. New-hire retention generally met target: 87.2% versus 86%, with exceptions.
3. Annual regretted turnover met the 7.5% maximum, but rose to 5.0% in 2025.

Explain the senior warning:

“Every senior country-quarter group is small. One person can move a quarterly percentage sharply, so I trust the broad multi-period concern more than one isolated quarterly rate.”

### Slide 9, about 1 minute

Explain Spearman without statistical jargon:

“Spearman asks whether two measures generally move in the same order. A result near plus one means they rise together, near minus one means one tends to rise while the other falls, and near zero means there is no consistent ordering.”

Then state the conclusion:

“Most results are close to zero. The furthest is -0.263, which is still only a descriptive association. The responsible finding is that these indicators do not clearly explain the workforce results.”

## 4. Tradeoffs, AI usage, and next steps, 3 minutes

### Slide 10, about 2 minutes

Spend about 45 seconds on tradeoffs. Use one sentence each:

- DuckDB gives local analytical SQL without operating a server.
- Streamlit makes the required interactive evidence quick to inspect; Power BI is the production mapping.
- Spearman is easier to explain and defend than an unnecessary prediction model.
- Small groups stay visible but visibly warned.

Spend about 1 minute 15 seconds on AI accountability:

“I did not ask an agent to produce a finished black box. I approved small contracts, reviewed results, questioned decisions, and required tests and source evidence. One important correction came from my review: the first plan started economic data in 2021, but trailing 2021 turnover needs 2020 context. I challenged that, approved the extension, and verified that the missing trailing windows disappeared.”

Also mention the materially changed suggestion:

“We considered committing every generated CSV and database as offline evidence. I approved a smaller approach instead: reviewed provider responses with checksums. That tests parsing and avoids storing duplicated derived answers.”

### Slide 11, about 1 minute

Do not promise features. Explain the order:

1. Investigate the senior-retention concern with HR and privacy-safe groups.
2. Improve explanatory data only with governance and business agreement.
3. Define operating ownership before production deployment.
4. Scale the tested rules only when volume and governance justify it.

Close with:

“The solution is intentionally small, reproducible, and explainable. It answers the three objectives, preserves evidence, exposes uncertainty, and avoids turning weak associations into causal stories.”

## Likely questions and short answers

### Why DuckDB rather than SQL Server?

DuckDB gives this small local analytical project SQL, typed tables, joins, and aggregation without installing or operating a server. SQL Server becomes more appropriate when several users, central security, continuous service, and enterprise administration are required.

### Why not use SQLite?

SQLite would work for storage, but DuckDB is designed for analytical queries and works naturally with pandas and column-oriented scans. SQLite is strongest for application transactions, such as many small inserts and updates.

### Why Spearman correlation?

The sample is small, percentages are bounded, and a straight-line relationship is not guaranteed. Spearman checks general ordered movement and is easier to explain. It still does not prove causation.

### Why are business-unit relationships not separate statistical samples?

The external indicators are national. Repeating one country-quarter economic value for every business unit would make the sample look larger without adding independent economic evidence.

### Why keep rows that cannot support a metric?

They remain useful as quality and audit evidence, and a row may still support a calculation that does not require the missing field. The project excludes records only from calculations they cannot safely support.

### Why use 2020 external data when objectives start in 2021?

The first 2021 turnover result looks backward across 12 months. It needs economic context from 2020 to describe the same window. The 2020 data supports the calculation but does not create a 2020 workforce result.

### Why not build a predictive model?

The assessment asks for defensible analysis, and the dataset lacks many possible employee-level explanations. A predictive model would add complexity and could create false confidence without proving why outcomes happened.

### What does “current data vintage” mean?

It means the public values as they existed when downloaded. Statistical agencies can revise history, so the project records retrieval evidence and does not claim the current value was known during the period it describes.

### What would fail safely?

A missing input, changed replay checksum, incomplete external grid, or failed pipeline stage stops the run with a named error. DuckDB is rebuilt last, so an earlier failure does not overwrite the previous working database.

### What is the largest limitation?

The workforce file has limited explanatory detail and no transfer history, while economic indicators are national. The results can identify patterns and areas for investigation, but they cannot establish individual causes.
