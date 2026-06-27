"""Load NPDB Public Use Data File CSV inputs."""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl

# NPDB CSV format notes (from HRSA public documentation, verified June 2026):
# - Header row present with lowercase column names (54 columns)
# - Encoding: ASCII/UTF-8 (no BOM observed in documentation)
# - Dollar fields (payment, totalpmt): DOLLAR12 with embedded $; CSV omits commas (e.g. "$97500")
# - Missing values: blank/empty strings; some numeric sentinels (998, 999) in categorical fields
# - Download may be a ZIP archive containing a single NPDBYYMM.CSV file
# - Line endings: CRLF or LF; Polars handles both
# - Column order matches specification but should not be relied upon; match by name


class LoaderError(Exception):
    """Raised when input files cannot be read."""


def resolve_csv_path(input_path: Path) -> Path:
    if not input_path.exists():
        msg = f"Input path does not exist: {input_path}"
        raise LoaderError(msg)

    if input_path.suffix.lower() == ".csv":
        return input_path

    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path) as archive:
            csv_members = [
                name
                for name in archive.namelist()
                if name.lower().endswith(".csv") and not name.startswith("__MACOSX")
            ]
            if not csv_members:
                msg = f"No CSV file found inside ZIP archive: {input_path}"
                raise LoaderError(msg)
            if len(csv_members) > 1:
                csv_members.sort()
            member = csv_members[0]
            extract_dir = input_path.parent / f".{input_path.stem}_extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            target = extract_dir / Path(member).name
            with archive.open(member) as source, target.open("wb") as dest:
                dest.write(source.read())
            return target

    msg = (
        f"Unsupported input format: {input_path.suffix}. "
        "Provide a .csv file or .zip archive containing a CSV."
    )
    raise LoaderError(msg)


def read_npdb_csv(input_path: Path) -> pl.DataFrame:
    csv_path = resolve_csv_path(input_path)
    try:
        frame = pl.read_csv(
            csv_path,
            infer_schema_length=10_000,
            null_values=["", " ", "NA", "N/A"],
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"Failed to read CSV file {csv_path}: {exc}"
        raise LoaderError(msg) from exc

    frame = frame.rename({column: column.lower().strip() for column in frame.columns})
    return frame


def read_npdb_input(input_path: Path) -> pl.DataFrame:
    suffix = input_path.suffix.lower()
    if suffix == ".parquet":
        return pl.read_parquet(input_path)
    return read_npdb_csv(input_path)
