from __future__ import annotations

from pathlib import Path

import duckdb


class LakehouseService:
    def query_csv(self, file_path: str | Path, sql: str) -> tuple[list[str], list[dict[str, object]]]:
        """Run ad hoc SQL against a CSV by mounting it as a DuckDB view.

        DuckDB keeps the lakehouse slice lightweight while still giving analysts
        a familiar SQL interface over file-based datasets.
        """

        dataset_path = Path(file_path)
        if not dataset_path.exists():
            raise FileNotFoundError(dataset_path)

        connection = duckdb.connect(database=":memory:")
        escaped_path = str(dataset_path).replace("'", "''")
        connection.execute(f"CREATE VIEW dataset AS SELECT * FROM read_csv_auto('{escaped_path}')")
        cursor = connection.execute(sql)
        columns = [column[0] for column in (cursor.description or [])]
        rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        return columns, rows