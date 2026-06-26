"""Normalize NPDB columns and cast types."""

from __future__ import annotations

import polars as pl

from npdb_kit.schema import ColumnSpec, SchemaSpec

DOLLAR_CLEAN_PATTERN = r"[^0-9.\-]"


def _cast_column(frame: pl.DataFrame, column: ColumnSpec) -> pl.Series:
    series = frame.get_column(column.name)

    if column.dollar:
        cleaned = (
            series.cast(pl.Utf8, strict=False)
            .fill_null("")
            .str.strip_chars()
            .str.replace_all(DOLLAR_CLEAN_PATTERN, "")
        )
        return cleaned.cast(pl.Float64, strict=False)

    if column.dtype == "int64":
        return series.cast(pl.Int64, strict=False)
    if column.dtype == "int32":
        return series.cast(pl.Int32, strict=False)
    if column.dtype == "float64":
        return series.cast(pl.Float64, strict=False)
    return series.cast(pl.Utf8, strict=False)


def transform(
    frame: pl.DataFrame,
    schema: SchemaSpec,
    *,
    include_practnum: bool = False,
) -> pl.DataFrame:
    normalized = frame.rename({name: name.lower().strip() for name in frame.columns})
    missing = [column.name for column in schema.columns if column.name not in normalized.columns]
    if missing:
        msg = f"Cannot transform frame; missing columns: {', '.join(missing)}"
        raise ValueError(msg)

    casted_columns: list[pl.Series] = []
    for column in schema.columns:
        casted_columns.append(_cast_column(normalized, column).alias(column.name))

    result = pl.DataFrame(casted_columns)

    if not include_practnum and "practnum" in result.columns:
        result = result.drop("practnum")

    return result
