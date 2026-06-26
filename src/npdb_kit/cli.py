"""Command-line interface for npdb-public-data-kit."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from npdb_kit.duckdb_builder import build_duckdb
from npdb_kit.loader import LoaderError, read_npdb_input
from npdb_kit.schema import load_schema
from npdb_kit.transformer import transform
from npdb_kit.validator import ValidationResult, validate_frame, write_validation_report

app = typer.Typer(
    name="npdb-kit",
    help="NPDB Public Use Data Kit — aggregate analysis toolkit for HRSA public data.",
    no_args_is_help=True,
)
console = Console()


def _run_validation(frame, schema, input_file: str) -> ValidationResult:
    return validate_frame(frame, schema, input_file=input_file)


@app.command()
def build(
    input: Annotated[Path, typer.Argument(help="Path to NPDB CSV or ZIP file")],
    output: Annotated[Path, typer.Option(help="Output directory")] = Path("./output"),
    include_practnum: Annotated[
        bool,
        typer.Option(help="Include practnum column (see compliance warning in README)"),
    ] = False,
) -> None:
    """Load NPDB CSV, validate, export Parquet, and build DuckDB warehouse."""
    if include_practnum:
        console.print(
            "[yellow]Warning:[/yellow] practnum is a file-specific pseudonym. "
            "Use only for approved aggregate research workflows."
        )

    schema = load_schema()
    try:
        raw = read_npdb_input(input)
    except LoaderError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        full_frame = transform(raw, schema, include_practnum=True)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    result = _run_validation(full_frame, schema, input_file=str(input))
    export_frame = full_frame if include_practnum else full_frame.drop("practnum")
    output.mkdir(parents=True, exist_ok=True)

    parquet_path = output / "npdb_reports.parquet"
    export_frame.write_parquet(parquet_path)

    report_path = output / "validation.md"
    write_validation_report(result, schema, report_path)

    db_path = output / "npdb.duckdb"
    build_duckdb(parquet_path, db_path, schema)

    if result.passed:
        console.print(f"[green]Build complete.[/green] Output written to {output}")
    else:
        console.print(
            f"[yellow]Build finished with validation failures.[/yellow] See {report_path}"
        )
        raise typer.Exit(code=1)


@app.command()
def validate(
    input: Annotated[Path, typer.Argument(help="Path to NPDB CSV, ZIP, or Parquet")],
    output: Annotated[Path, typer.Option(help="Validation report output path")] = Path(
        "./output/validation.md"
    ),
) -> None:
    """Run schema and quality checks. Write Markdown report."""
    schema = load_schema()
    try:
        raw = read_npdb_input(input)
    except LoaderError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    try:
        frame = transform(raw, schema, include_practnum=True)
    except ValueError:
        frame = raw.rename({name: name.lower().strip() for name in raw.columns})

    result = _run_validation(frame, schema, input_file=str(input))
    write_validation_report(result, schema, output)

    if result.passed:
        console.print(f"[green]Validation passed.[/green] Report: {output}")
    else:
        console.print(f"[red]Validation failed.[/red] Report: {output}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
