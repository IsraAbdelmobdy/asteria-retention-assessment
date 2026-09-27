"""Read and integrity-check the supplied synthetic assessment package."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


class InputContractError(ValueError):
    """Raised when a supplied artifact does not match its declared contract."""


@dataclass(frozen=True)
class ArtifactCheck:
    name: str
    expected_bytes: int
    actual_bytes: int
    expected_data_rows: int
    actual_data_rows: int
    expected_sha256: str
    actual_sha256: str
    valid: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SuppliedData:
    events: pd.DataFrame
    objectives: pd.DataFrame
    dictionary: pd.DataFrame
    artifact_checks: tuple[ArtifactCheck, ...]
    manifest: dict[str, object]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        row_count = sum(1 for _ in csv.reader(stream))
    return max(row_count - 1, 0)


def verify_assessment_package(input_dir: Path) -> tuple[dict[str, object], tuple[ArtifactCheck, ...]]:
    manifest_path = input_dir / "assessment_data_manifest.json"
    if not manifest_path.is_file():
        raise InputContractError(f"missing manifest: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as stream:
        manifest = json.load(stream)

    declared_files = manifest.get("files")
    if not isinstance(declared_files, list) or not declared_files:
        raise InputContractError("manifest must declare at least one file")

    checks: list[ArtifactCheck] = []
    for declaration in declared_files:
        name = str(declaration["name"])
        path = input_dir / name
        if not path.is_file():
            raise InputContractError(f"missing declared artifact: {path}")

        check = ArtifactCheck(
            name=name,
            expected_bytes=int(declaration["bytes"]),
            actual_bytes=path.stat().st_size,
            expected_data_rows=int(declaration["data_rows"]),
            actual_data_rows=_csv_data_rows(path),
            expected_sha256=str(declaration["sha256"]).lower(),
            actual_sha256=_sha256(path),
            valid=False,
        )
        check = ArtifactCheck(
            **{
                **check.as_dict(),
                "valid": (
                    check.expected_bytes == check.actual_bytes
                    and check.expected_data_rows == check.actual_data_rows
                    and check.expected_sha256 == check.actual_sha256
                ),
            }
        )
        checks.append(check)

    invalid = [check.name for check in checks if not check.valid]
    if invalid:
        raise InputContractError(
            "artifact integrity check failed for: " + ", ".join(sorted(invalid))
        )

    return manifest, tuple(checks)


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )


def load_supplied_data(input_dir: Path) -> SuppliedData:
    manifest, checks = verify_assessment_package(input_dir)
    return SuppliedData(
        events=_read_csv(input_dir / "employee_lifecycle_events.csv"),
        objectives=_read_csv(input_dir / "retention_objectives.csv"),
        dictionary=_read_csv(input_dir / "data_dictionary.csv"),
        artifact_checks=checks,
        manifest=manifest,
    )

