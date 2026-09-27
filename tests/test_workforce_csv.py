import json
from pathlib import Path

import pytest

from asteria_retention.adapters.workforce_csv import (
    InputContractError,
    verify_assessment_package,
)


def test_checked_in_assessment_package_matches_manifest():
    manifest, checks = verify_assessment_package(Path("data/input"))

    assert manifest["workforce_as_of_date"] == "2025-12-31"
    assert len(checks) == 3
    assert all(check.valid for check in checks)


def test_modified_artifact_fails_integrity_check(tmp_path):
    source_dir = Path("data/input")
    for source in source_dir.iterdir():
        if source.is_file():
            (tmp_path / source.name).write_bytes(source.read_bytes())

    events = tmp_path / "employee_lifecycle_events.csv"
    events.write_bytes(events.read_bytes() + b"\n")

    with pytest.raises(InputContractError, match="employee_lifecycle_events.csv"):
        verify_assessment_package(tmp_path)

