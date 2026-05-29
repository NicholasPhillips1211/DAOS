from __future__ import annotations

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Tuple, List, Dict

import duckdb


class LakehouseService:
    def query_csv(self, file_path: str | Path, sql: str, max_rows: int = 1000, timeout_seconds: float = 5.0) -> tuple[List[str], List[Dict[str, object]]]:
        """Run SQL against a CSV using DuckDB with a timeout and row limit.

        Safety measures (timeout + max_rows) prevent expensive or accidental
        full-file scans from degrading the API server.
        """

        dataset_path = Path(file_path)
        if not dataset_path.exists():
            raise FileNotFoundError(dataset_path)

        def _run_query() -> Tuple[List[str], List[Dict[str, object]]]:
            conn = duckdb.connect(database=":memory:")
            escaped_path = str(dataset_path).replace("'", "''")
            conn.execute(f"CREATE VIEW dataset AS SELECT * FROM read_csv_auto('{escaped_path}')")
            cursor = conn.execute(sql)
            columns = [column[0] for column in (cursor.description or [])]
            rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
            return columns, rows

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_query)
            try:
                columns, rows = future.result(timeout=timeout_seconds)
            except TimeoutError:
                future.cancel()
                raise RuntimeError("Query timed out")

        if len(rows) > max_rows:
            # Truncate results to the configured maximum to avoid huge responses.
            rows = rows[:max_rows]

        return columns, rows