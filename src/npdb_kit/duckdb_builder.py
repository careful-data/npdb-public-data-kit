"""Build DuckDB warehouse from cleaned NPDB Parquet."""

from __future__ import annotations

from pathlib import Path

import duckdb

from npdb_kit.schema import SchemaSpec, sql_dir

VIEW_FILES = (
    "reports_by_year.sql",
    "reports_by_state.sql",
    "reports_by_record_type.sql",
    "malpractice_payment_trends.sql",
)


def build_duckdb(
    parquet_path: Path,
    db_path: Path,
    schema: SchemaSpec,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = duckdb.connect(str(db_path))
    try:
        connection.execute(
            """
            CREATE TABLE npdb_reports AS
            SELECT * FROM read_parquet(?)
            """,
            [str(parquet_path)],
        )

        views_path = sql_dir() / "views"
        for view_file in VIEW_FILES:
            sql = (views_path / view_file).read_text(encoding="utf-8")
            sql = sql.replace("{{threshold}}", str(schema.cell_suppression_threshold))
            connection.execute(sql)
    finally:
        connection.close()
