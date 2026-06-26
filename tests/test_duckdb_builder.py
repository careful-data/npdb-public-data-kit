from __future__ import annotations

import duckdb

from npdb_kit.duckdb_builder import build_duckdb
from npdb_kit.loader import read_npdb_csv
from npdb_kit.transformer import transform


def test_build_duckdb_creates_views(sample_csv, schema, tmp_path) -> None:
    raw = read_npdb_csv(sample_csv)
    cleaned = transform(raw, schema, include_practnum=True)
    parquet_path = tmp_path / "npdb_reports.parquet"
    cleaned.write_parquet(parquet_path)
    db_path = tmp_path / "npdb.duckdb"

    build_duckdb(parquet_path, db_path, schema)
    assert db_path.exists()

    connection = duckdb.connect(str(db_path))
    try:
        views = {
            row[0]
            for row in connection.execute(
                "SELECT view_name FROM duckdb_views() WHERE schema_name = 'main'"
            ).fetchall()
        }
        assert "v_reports_by_year" in views
        assert "v_reports_by_state" in views
        assert "v_reports_by_record_type" in views
        assert "v_malpractice_payment_trends" in views

        suppressed = connection.execute("SELECT COUNT(*) FROM v_reports_by_year").fetchone()[0]
        assert suppressed >= 0
    finally:
        connection.close()
