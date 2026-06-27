from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from npdb_kit.loader import LoaderError, read_npdb_csv, resolve_csv_path
from npdb_kit.schema import load_schema


def test_read_sample_csv(sample_csv: Path) -> None:
    frame = read_npdb_csv(sample_csv)
    schema = load_schema()
    assert frame.height == 100
    assert len(frame.columns) == len(schema.column_names)


def test_read_csv_from_zip(sample_csv: Path, tmp_path: Path) -> None:
    zip_path = tmp_path / "npdb.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.write(sample_csv, arcname="NPDB2603.CSV")
    frame = read_npdb_csv(zip_path)
    assert frame.height == 100


def test_reject_unsupported_format(tmp_path: Path) -> None:
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("not npdb", encoding="utf-8")
    with pytest.raises(LoaderError):
        resolve_csv_path(bad_file)


def test_column_names_lowercased(sample_csv: Path) -> None:
    frame = read_npdb_csv(sample_csv)
    assert all(name == name.lower() for name in frame.columns)
