from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from npdb_kit.cli import app

runner = CliRunner()


def test_build_strips_practnum_by_default(sample_csv: Path, tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = runner.invoke(app, ["build", str(sample_csv), "--output", str(output)])
    assert result.exit_code == 0, result.stdout

    import polars as pl

    frame = pl.read_parquet(output / "npdb_reports.parquet")
    assert "practnum" not in frame.columns


def test_build_command_creates_outputs(sample_csv: Path, tmp_path: Path) -> None:
    output = tmp_path / "output"
    result = runner.invoke(app, ["build", str(sample_csv), "--output", str(output)])
    assert result.exit_code == 0, result.stdout
    assert (output / "npdb_reports.parquet").exists()
    assert (output / "validation.md").exists()
    assert (output / "npdb.duckdb").exists()


def test_validate_command_writes_report(sample_csv: Path, tmp_path: Path) -> None:
    report = tmp_path / "validation.md"
    result = runner.invoke(app, ["validate", str(sample_csv), "--output", str(report)])
    assert result.exit_code == 0, result.stdout
    assert report.exists()
