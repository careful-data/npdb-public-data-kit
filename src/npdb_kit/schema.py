"""Load and resolve NPDB schema definitions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str
    nullable: bool
    description: str
    allowed_values: tuple[str, ...] | None = None
    code_map: str | None = None
    value_range: tuple[int | None, int | None] | None = None
    dollar: bool = False
    sensitive: bool = False


@dataclass(frozen=True)
class SchemaSpec:
    version: str
    source_url: str
    expected_row_count: int | None
    cell_suppression_threshold: int
    columns: tuple[ColumnSpec, ...]

    @property
    def column_names(self) -> list[str]:
        return [column.name for column in self.columns]

    def column_by_name(self, name: str) -> ColumnSpec | None:
        for column in self.columns:
            if column.name == name:
                return column
        return None


def schema_dir() -> Path:
    candidates = [
        PACKAGE_DIR / "schema",
        Path.cwd() / "schema",
    ]
    for candidate in candidates:
        if (candidate / "npdb_schema.yaml").exists():
            return candidate
    msg = "Could not locate schema directory (expected npdb_schema.yaml)."
    raise FileNotFoundError(msg)


def sql_dir() -> Path:
    candidates = [
        PACKAGE_DIR / "sql",
        Path.cwd() / "sql",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    msg = "Could not locate sql directory."
    raise FileNotFoundError(msg)


def load_schema(schema_path: Path | None = None) -> SchemaSpec:
    path = schema_path or (schema_dir() / "npdb_schema.yaml")
    with path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    columns: list[ColumnSpec] = []
    for entry in raw["columns"]:
        value_range = None
        if "range" in entry:
            low, high = entry["range"]
            value_range = (low, high)
        columns.append(
            ColumnSpec(
                name=entry["name"],
                dtype=entry["type"],
                nullable=entry.get("nullable", True),
                description=entry.get("description", ""),
                allowed_values=tuple(entry["allowed_values"])
                if "allowed_values" in entry
                else None,
                code_map=entry.get("code_map"),
                value_range=value_range,
                dollar=entry.get("dollar", False),
                sensitive=entry.get("sensitive", False),
            )
        )

    return SchemaSpec(
        version=raw["version"],
        source_url=raw["source_url"],
        expected_row_count=raw.get("expected_row_count"),
        cell_suppression_threshold=raw.get("cell_suppression_threshold", 11),
        columns=tuple(columns),
    )


def load_code_map(code_map_name: str) -> dict[str, str]:
    path = schema_dir() / "code_maps" / code_map_name
    with path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)
    values = raw.get("values", {})
    return {str(key): str(label) for key, label in values.items()}


def check_column_presence(
    actual_columns: list[str], schema: SchemaSpec
) -> tuple[list[str], list[str], list[str]]:
    expected = set(schema.column_names)
    actual = {name.lower() for name in actual_columns}
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    present = sorted(expected & actual)
    return present, missing, extra
