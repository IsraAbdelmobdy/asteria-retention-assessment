"""Small atomic file writers shared by pipeline steps."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd


def atomic_write_bytes(destination: Path, content: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="asteria-external-", dir=destination.parent
    ) as temp:
        source = Path(temp) / destination.name
        source.write_bytes(content)
        source.replace(destination)


def atomic_write_csv(destination: Path, frame: pd.DataFrame) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="asteria-external-", dir=destination.parent
    ) as temp:
        source = Path(temp) / destination.name
        frame.to_csv(source, index=False)
        source.replace(destination)
