"""Small command-line boundary for reproducible local workflows."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from asteria_retention.config import ConfigError, load_project_config
from asteria_retention.adapters.workforce_csv import InputContractError
from asteria_retention.domain.quality import WorkforceContractError
from asteria_retention.pipeline.workforce_quality import prepare_workforce
from asteria_retention.domain.retention import RetentionContractError
from asteria_retention.pipeline.new_hire_retention import (
    prepare_new_hire_six_month_retention,
)
from asteria_retention.pipeline.senior_hire_retention import (
    prepare_senior_hire_twelve_month_retention,
)
from asteria_retention.pipeline.regretted_turnover import (
    prepare_regretted_turnover_twelve_month,
)
from asteria_retention.adapters.eurostat import EurostatSourceError
from asteria_retention.pipeline.unemployment import ingest_unemployment
from asteria_retention.pipeline.job_vacancy import ingest_job_vacancy
from asteria_retention.adapters.world_bank import WorldBankSourceError
from asteria_retention.pipeline.inflation import ingest_inflation
from asteria_retention.storage.duckdb_store import DatabaseBuildError, build_database
from asteria_retention.pipeline.combined_context import (
    CombinedContextError,
    build_combined_context,
)
from asteria_retention.pipeline.association_analysis import (
    AssociationAnalysisError,
    build_association_analysis,
)
from asteria_retention.pipeline.core import CorePipelineError, run_core_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asteria-retention",
        description="Asteria workforce-retention and external-signals data product.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run the complete reproducible workflow and rebuild DuckDB last.",
    )
    run.add_argument("--project-root", type=Path, default=Path.cwd())
    run.add_argument("--input-dir", type=Path, default=Path("data/input"))
    run.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    run.add_argument("--canonical-dir", type=Path, default=Path("data/canonical"))
    run.add_argument("--output-dir", type=Path, default=Path("data/output"))
    run.add_argument(
        "--database-path",
        type=Path,
        default=Path("data/output/asteria.duckdb"),
    )
    run.add_argument(
        "--offline",
        action="store_true",
        help="Reuse and validate prepared external files without API calls.",
    )

    validate = subparsers.add_parser(
        "validate-config",
        help="Validate the checked-in indicator and quality configuration.",
    )
    validate.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing the config directory.",
    )

    prepare = subparsers.add_parser(
        "prepare-workforce",
        help="Verify, canonicalise, and quality-check the supplied workforce data.",
    )
    prepare.add_argument("--input-dir", type=Path, default=Path("data/input"))
    prepare.add_argument("--canonical-dir", type=Path, default=Path("data/canonical"))
    prepare.add_argument("--output-dir", type=Path, default=Path("data/output"))

    new_hire = subparsers.add_parser(
        "calculate-new-hire-retention",
        help="Prepare workforce data and calculate the approved six-month new-hire objective.",
    )
    new_hire.add_argument("--input-dir", type=Path, default=Path("data/input"))
    new_hire.add_argument("--canonical-dir", type=Path, default=Path("data/canonical"))
    new_hire.add_argument("--output-dir", type=Path, default=Path("data/output"))

    senior_hire = subparsers.add_parser(
        "calculate-senior-hire-retention",
        help="Prepare workforce data and calculate the approved twelve-month senior-hire objective.",
    )
    senior_hire.add_argument("--input-dir", type=Path, default=Path("data/input"))
    senior_hire.add_argument("--canonical-dir", type=Path, default=Path("data/canonical"))
    senior_hire.add_argument("--output-dir", type=Path, default=Path("data/output"))

    turnover = subparsers.add_parser(
        "calculate-regretted-turnover",
        help="Prepare workforce data and calculate trailing-twelve-month regretted turnover.",
    )
    turnover.add_argument("--input-dir", type=Path, default=Path("data/input"))
    turnover.add_argument("--canonical-dir", type=Path, default=Path("data/canonical"))
    turnover.add_argument("--output-dir", type=Path, default=Path("data/output"))

    unemployment = subparsers.add_parser(
        "ingest-unemployment",
        help="Download and prepare the approved Eurostat unemployment indicator.",
    )
    unemployment.add_argument("--project-root", type=Path, default=Path.cwd())
    unemployment.add_argument(
        "--raw-dir", type=Path, default=Path("data/raw/eurostat")
    )
    unemployment.add_argument(
        "--canonical-dir", type=Path, default=Path("data/canonical")
    )
    unemployment.add_argument("--output-dir", type=Path, default=Path("data/output"))

    vacancy = subparsers.add_parser(
        "ingest-job-vacancy",
        help="Download and preserve the approved Eurostat quarterly job-vacancy indicator.",
    )
    vacancy.add_argument("--project-root", type=Path, default=Path.cwd())
    vacancy.add_argument("--raw-dir", type=Path, default=Path("data/raw/eurostat"))
    vacancy.add_argument(
        "--canonical-dir", type=Path, default=Path("data/canonical")
    )
    vacancy.add_argument("--output-dir", type=Path, default=Path("data/output"))

    inflation = subparsers.add_parser(
        "ingest-inflation",
        help="Download and preserve approved annual World Bank consumer-price inflation.",
    )
    inflation.add_argument("--project-root", type=Path, default=Path.cwd())
    inflation.add_argument(
        "--raw-dir", type=Path, default=Path("data/raw/world_bank")
    )
    inflation.add_argument(
        "--canonical-dir", type=Path, default=Path("data/canonical")
    )
    inflation.add_argument("--output-dir", type=Path, default=Path("data/output"))

    database = subparsers.add_parser(
        "build-database",
        help="Build the local DuckDB file from all prepared workforce and external outputs.",
    )
    database.add_argument(
        "--canonical-dir", type=Path, default=Path("data/canonical")
    )
    database.add_argument("--output-dir", type=Path, default=Path("data/output"))
    database.add_argument(
        "--database-path",
        type=Path,
        default=Path("data/output/asteria.duckdb"),
    )

    combined = subparsers.add_parser(
        "build-combined-context",
        help="Align workforce results with quarterly labour context and annual inflation.",
    )
    combined.add_argument(
        "--canonical-dir", type=Path, default=Path("data/canonical")
    )
    combined.add_argument("--output-dir", type=Path, default=Path("data/output"))

    association = subparsers.add_parser(
        "analyze-associations",
        help="Calculate the approved country-total workforce/economic associations.",
    )
    association.add_argument("--output-dir", type=Path, default=Path("data/output"))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        mode = "offline" if args.offline else "online"
        print(f"Starting complete {mode} workflow...")
        try:
            result = run_core_pipeline(
                project_root=args.project_root,
                input_dir=args.input_dir,
                raw_dir=args.raw_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
                database_path=args.database_path,
                offline=args.offline,
                progress=lambda stage: print(f"  Running: {stage}"),
            )
        except CorePipelineError as exc:
            print(f"Core workflow failed: {exc}")
            return 2
        print(
            "Core workflow succeeded: "
            f"{len(result.completed_stages)} stages completed; "
            f"database rebuilt at {result.database_path}."
        )
        return 0

    if args.command == "validate-config":
        try:
            config = load_project_config(args.project_root)
        except ConfigError as exc:
            print(f"Configuration is invalid: {exc}")
            return 2

        country_count = len(config["indicators"]["countries"])
        indicator_count = len(config["indicators"]["indicators"])
        print(
            "Configuration is valid: "
            f"{country_count} countries, {indicator_count} indicators."
        )
        return 0

    if args.command == "calculate-new-hire-retention":
        try:
            result = prepare_new_hire_six_month_retention(
                input_dir=args.input_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (
            InputContractError,
            WorkforceContractError,
            RetentionContractError,
            OSError,
        ) as exc:
            print(f"New-hire retention calculation failed: {exc}")
            return 2

        rate = result.summary["overall_retention_rate"]
        print(
            "Six-month new-hire retention succeeded: "
            f"{result.summary['eligible_hires']} eligible hires, "
            f"{result.summary['not_yet_measurable_hires']} not yet measurable, "
            f"overall retention {rate:.1%}."
        )
        return 0

    if args.command == "calculate-senior-hire-retention":
        try:
            result = prepare_senior_hire_twelve_month_retention(
                input_dir=args.input_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (
            InputContractError,
            WorkforceContractError,
            RetentionContractError,
            OSError,
        ) as exc:
            print(f"Senior-hire retention calculation failed: {exc}")
            return 2

        rate = result.summary["overall_retention_rate"]
        print(
            "Twelve-month senior-hire retention succeeded: "
            f"{result.summary['eligible_hires']} eligible senior hires, "
            f"{result.summary['not_yet_measurable_hires']} not yet measurable, "
            f"overall retention {rate:.1%}."
        )
        return 0

    if args.command == "calculate-regretted-turnover":
        try:
            result = prepare_regretted_turnover_twelve_month(
                input_dir=args.input_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (
            InputContractError,
            WorkforceContractError,
            RetentionContractError,
            OSError,
        ) as exc:
            print(f"Regretted-turnover calculation failed: {exc}")
            return 2

        print(
            "Trailing-twelve-month regretted turnover succeeded: "
            f"{result.summary['reporting_quarters']} reporting quarters, "
            f"{result.summary['country_quarter_rows']} country-quarter rows, "
            "each using 12 month-end headcounts."
        )
        return 0

    if args.command == "ingest-unemployment":
        try:
            result = ingest_unemployment(
                project_root=args.project_root,
                raw_dir=args.raw_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (ConfigError, EurostatSourceError, OSError) as exc:
            print(f"Unemployment ingestion failed: {exc}")
            return 2

        print(
            "Eurostat unemployment ingestion succeeded: "
            f"{result.summary['returned_monthly_rows']} monthly rows, "
            f"{result.summary['complete_quarters']} complete quarters, "
            f"{result.summary['incomplete_quarters']} incomplete quarters."
        )
        return 0

    if args.command == "ingest-job-vacancy":
        try:
            result = ingest_job_vacancy(
                project_root=args.project_root,
                raw_dir=args.raw_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (ConfigError, EurostatSourceError, OSError) as exc:
            print(f"Job-vacancy ingestion failed: {exc}")
            return 2

        print(
            "Eurostat job-vacancy ingestion succeeded: "
            f"{result.summary['returned_quarterly_rows']} quarterly rows, "
            f"{result.summary['provisional_values']} provisional values, "
            f"{result.summary['missing_quarterly_values']} missing values."
        )
        return 0

    if args.command == "ingest-inflation":
        try:
            result = ingest_inflation(
                project_root=args.project_root,
                raw_dir=args.raw_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (ConfigError, WorldBankSourceError, OSError) as exc:
            print(f"Inflation ingestion failed: {exc}")
            return 2

        print(
            "World Bank inflation ingestion succeeded: "
            f"{result.summary['canonical_annual_rows']} annual rows, "
            f"{result.summary['available_annual_values']} available values, "
            f"{result.summary['missing_annual_values']} missing values."
        )
        return 0

    if args.command == "build-database":
        try:
            result = build_database(
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
                database_path=args.database_path,
            )
        except DatabaseBuildError as exc:
            print(f"DuckDB build failed: {exc}")
            return 2

        print(
            "DuckDB build succeeded: "
            f"{len(result.loads) + 1} tables loaded into {result.database_path}."
        )
        return 0

    if args.command == "build-combined-context":
        try:
            result = build_combined_context(
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (CombinedContextError, OSError) as exc:
            print(f"Combined-context build failed: {exc}")
            return 2

        print(
            "Combined-context build succeeded: "
            f"{result.summary['quarterly_rows']} quarterly rows, "
            f"{result.summary['annual_rows']} annual rows, "
            f"{result.summary['incomplete_trailing_external_country_quarters']} "
            "incomplete early trailing country-quarters."
        )
        return 0

    if args.command == "analyze-associations":
        try:
            result = build_association_analysis(output_dir=args.output_dir)
        except (AssociationAnalysisError, OSError) as exc:
            print(f"Association analysis failed: {exc}")
            return 2

        print(
            "Association analysis succeeded: "
            f"{result.summary['calculated_associations']} of "
            f"{result.summary['association_count']} comparisons calculated."
        )
        return 0

    if args.command == "prepare-workforce":
        try:
            result = prepare_workforce(
                input_dir=args.input_dir,
                canonical_dir=args.canonical_dir,
                output_dir=args.output_dir,
            )
        except (InputContractError, WorkforceContractError, OSError) as exc:
            print(f"Workforce preparation failed: {exc}")
            return 2

        print(
            "Workforce preparation succeeded: "
            f"{result.summary['analytical_rows']} analytical rows, "
            f"{result.summary['metric_ineligible_rows']} metric-ineligible rows, "
            f"{result.summary['hard_quarantined_rows']} hard-quarantined rows, "
            f"{result.summary['exact_duplicate_rows_removed']} duplicate rows removed."
        )
        return 0

    return 2
