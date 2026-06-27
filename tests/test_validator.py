from __future__ import annotations

import polars as pl

from npdb_kit.loader import read_npdb_csv
from npdb_kit.transformer import transform
from npdb_kit.validator import CheckStatus, validate_frame, write_validation_report


def test_validate_passes_on_sample(sample_csv, schema, tmp_path) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema, include_practnum=True)
    result = validate_frame(cleaned, schema, input_file=str(sample_csv))
    assert result.passed
    report_path = tmp_path / "validation.md"
    write_validation_report(result, schema, report_path)
    assert report_path.exists()
    assert "NPDB Validation Report" in report_path.read_text(encoding="utf-8")


def test_validate_fails_on_missing_column(schema) -> None:
    frame = pl.DataFrame({"seqno": [1, 2], "rectype": ["P", "C"]})
    result = validate_frame(frame, schema)
    assert not result.passed
    assert any(check.status == CheckStatus.FAIL for check in result.checks)


def test_validate_fails_when_reptype_unknown(schema, sample_csv) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema, include_practnum=True)
    cleaned = cleaned.with_columns(pl.lit(99999).alias("reptype"))
    result = validate_frame(cleaned, schema, input_file=str(sample_csv))
    assert any(
        check.name == "reptype_values" and check.status == CheckStatus.WARN
        for check in result.checks
    )
