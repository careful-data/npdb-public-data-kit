"""Data quality validation for NPDB Public Use Data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

import polars as pl

from npdb_kit.schema import SchemaSpec, check_column_presence, load_code_map


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    INFO = "INFO"


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    status: CheckStatus
    details: str


@dataclass(frozen=True)
class ValidationResult:
    checks: tuple[ValidationCheck, ...]
    row_count: int
    input_file: str

    @property
    def passed(self) -> bool:
        return all(check.status != CheckStatus.FAIL for check in self.checks)

    @property
    def warning_count(self) -> int:
        return sum(1 for check in self.checks if check.status == CheckStatus.WARN)

    @property
    def error_count(self) -> int:
        return sum(1 for check in self.checks if check.status == CheckStatus.FAIL)


NULL_RATE_WARN_THRESHOLD = 0.95


def validate_frame(
    frame: pl.DataFrame,
    schema: SchemaSpec,
    *,
    input_file: str = "unknown",
) -> ValidationResult:
    checks: list[ValidationCheck] = []
    row_count = frame.height

    present, missing, extra = check_column_presence(frame.columns, schema)
    if missing:
        checks.append(
            ValidationCheck(
                "column_presence",
                CheckStatus.FAIL,
                f"Missing columns: {', '.join(missing)}",
            )
        )
    else:
        checks.append(
            ValidationCheck(
                "column_presence",
                CheckStatus.PASS,
                f"{len(present)}/{len(schema.column_names)} columns found",
            )
        )

    if extra:
        checks.append(
            ValidationCheck(
                "extra_columns",
                CheckStatus.WARN,
                f"Unexpected columns: {', '.join(extra)}",
            )
        )
    else:
        checks.append(ValidationCheck("extra_columns", CheckStatus.PASS, "None"))

    cast_failures: list[str] = []
    for column in schema.columns:
        if column.name not in frame.columns:
            continue
        if column.dtype in {"int32", "int64", "float64"} and not column.dollar:
            null_before = frame.get_column(column.name).null_count()
            casted = frame.get_column(column.name).cast(
                pl.Int64 if column.dtype.startswith("int") else pl.Float64,
                strict=False,
            )
            null_after = casted.null_count()
            if null_after > null_before:
                cast_failures.append(column.name)

    if cast_failures:
        checks.append(
            ValidationCheck(
                "type_casting",
                CheckStatus.FAIL,
                f"Failed to cast columns: {', '.join(cast_failures)}",
            )
        )
    else:
        checks.append(
            ValidationCheck("type_casting", CheckStatus.PASS, "All columns cast successfully")
        )

    if "seqno" in frame.columns:
        duplicate_count = frame.height - frame.select("seqno").unique().height
        if duplicate_count > 0:
            checks.append(
                ValidationCheck(
                    "duplicate_seqno",
                    CheckStatus.FAIL,
                    f"{duplicate_count} duplicate seqno values",
                )
            )
        else:
            checks.append(ValidationCheck("duplicate_seqno", CheckStatus.PASS, "0 duplicates"))
    else:
        checks.append(
            ValidationCheck("duplicate_seqno", CheckStatus.WARN, "seqno column not available")
        )

    null_warnings: list[str] = []
    for column in schema.columns:
        if column.name not in frame.columns:
            continue
        null_rate = frame.get_column(column.name).null_count() / max(row_count, 1)
        if null_rate >= NULL_RATE_WARN_THRESHOLD and column.name not in {"workctry", "homectry"}:
            null_warnings.append(f"{column.name}: {null_rate:.1%}")
    if null_warnings:
        checks.append(
            ValidationCheck(
                "null_rates",
                CheckStatus.WARN,
                "; ".join(null_warnings[:5]),
            )
        )
    else:
        checks.append(ValidationCheck("null_rates", CheckStatus.PASS, "Within expected thresholds"))

    if "rectype" in frame.columns:
        allowed = {"A", "C", "M", "P"}
        invalid = (
            frame.filter(~pl.col("rectype").is_in(list(allowed)) & pl.col("rectype").is_not_null())
            .select("rectype")
            .unique()
            .to_series()
            .to_list()
        )
        if invalid:
            checks.append(
                ValidationCheck(
                    "rectype_values",
                    CheckStatus.FAIL,
                    f"Invalid rectype values: {invalid}",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    "rectype_values",
                    CheckStatus.PASS,
                    "All values in {A, C, M, P}",
                )
            )

    if "reptype" in frame.columns:
        allowed_codes = {int(code) for code in load_code_map("reptype.yaml")}
        invalid_codes = (
            frame.filter(pl.col("reptype").is_not_null())
            .select("reptype")
            .unique()
            .filter(~pl.col("reptype").is_in(list(allowed_codes)))
            .to_series()
            .to_list()
        )
        if invalid_codes:
            checks.append(
                ValidationCheck(
                    "reptype_values",
                    CheckStatus.WARN,
                    f"Unknown reptype codes: {invalid_codes[:10]}",
                )
            )
        else:
            checks.append(
                ValidationCheck("reptype_values", CheckStatus.PASS, "All values in known code set")
            )

    if "origyear" in frame.columns:
        current_year = datetime.now(tz=UTC).year
        out_of_range = frame.filter(
            pl.col("origyear").is_not_null()
            & ((pl.col("origyear") < 1990) | (pl.col("origyear") > current_year))
        ).height
        if out_of_range:
            checks.append(
                ValidationCheck(
                    "year_range",
                    CheckStatus.WARN,
                    f"{out_of_range} rows outside 1990-{current_year}",
                )
            )
        else:
            checks.append(ValidationCheck("year_range", CheckStatus.PASS, f"1990-{current_year}"))

    negative_payments = 0
    for payment_column in ("payment", "totalpmt"):
        if payment_column in frame.columns:
            negative_payments += frame.filter(pl.col(payment_column) < 0).height
    if negative_payments:
        checks.append(
            ValidationCheck(
                "payment_range",
                CheckStatus.WARN,
                f"{negative_payments} rows with negative payment values",
            )
        )
    else:
        checks.append(ValidationCheck("payment_range", CheckStatus.PASS, "No negative values"))

    checks.append(ValidationCheck("row_count", CheckStatus.INFO, f"{row_count:,} records"))

    return ValidationResult(checks=tuple(checks), row_count=row_count, input_file=input_file)


def render_markdown_report(result: ValidationResult, schema: SchemaSpec) -> str:
    status = "PASS" if result.passed else "FAIL"
    if result.passed and result.warning_count:
        status = f"PASS ({result.warning_count} warnings)"

    lines = [
        "# NPDB Validation Report",
        "",
        f"**File**: {result.input_file}",
        f"**Date**: {datetime.now(tz=UTC).date().isoformat()}",
        f"**Schema version**: {schema.version}",
        f"**Rows**: {result.row_count:,}",
        f"**Status**: {status}",
        "",
        "## Checks",
        "",
        "| Check | Status | Details |",
        "|-------|--------|---------|",
    ]
    for check in result.checks:
        lines.append(f"| {check.name} | {check.status.value} | {check.details} |")
    lines.append("")
    return "\n".join(lines)


def write_validation_report(
    result: ValidationResult,
    schema: SchemaSpec,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(result, schema), encoding="utf-8")
