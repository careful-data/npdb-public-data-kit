from __future__ import annotations

import polars as pl

from npdb_kit.loader import read_npdb_csv
from npdb_kit.transformer import transform


def test_transform_casts_payment(sample_csv, schema) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema)
    payment = cleaned.filter(pl.col("payment").is_not_null()).get_column("payment")
    assert payment.dtype == pl.Float64
    assert payment.min() >= 0


def test_transform_strips_practnum_by_default(sample_csv, schema) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema, include_practnum=False)
    assert "practnum" not in cleaned.columns


def test_transform_keeps_practnum_when_requested(sample_csv, schema) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema, include_practnum=True)
    assert "practnum" in cleaned.columns
