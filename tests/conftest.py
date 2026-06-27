"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from npdb_kit.schema import load_schema


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_csv(repo_root: Path) -> Path:
    return repo_root / "tests" / "fixtures" / "sample_npdb.csv"


@pytest.fixture
def schema():
    return load_schema()
