"""Test fixtures that work across the user and Codex Windows accounts."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def tmp_path() -> Iterator[Path]:
    """Provide an isolated folder and remove it when the test finishes.

    Pytest's default Windows temp root persists across runs. A folder created by
    the Codex sandbox account can therefore deny access to the normal user
    account, or vice versa. A unique self-cleaning directory avoids shared
    ownership while preserving the familiar tmp_path test interface.
    """

    with tempfile.TemporaryDirectory(prefix="asteria-test-") as directory:
        yield Path(directory)

