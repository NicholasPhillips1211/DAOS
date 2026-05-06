from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class InsightSummary:
    """Compact summary object returned by metric summarization."""

    title: str
    summary: str
    confidence: float


class AnalyticsService:
    def summarize_metric(self, name: str, value: float) -> InsightSummary:
        """Turn a raw metric into a stable, readable insight string.

        This keeps the analytics layer deterministic while leaving richer
        narrative generation to the business-translation layer.
        """

        return InsightSummary(title=name, summary=f"{name} is currently {value:.2f}.", confidence=0.8)

    def dataset_statistics(self, file_path: str | Path) -> dict[str, Any]:
        """Compute lightweight column statistics for an uploaded CSV dataset."""

        dataset_path = Path(file_path)
        with dataset_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        if not rows:
            return {"row_count": 0, "column_count": 0, "columns": []}

        columns = reader.fieldnames or []
        statistics_payload: list[dict[str, Any]] = []

        for column in columns:
            values = [(row.get(column) or "").strip() for row in rows]
            non_null_values = [value for value in values if value]
            numeric_values = [float(value) for value in non_null_values if self._is_number(value)]
            distinct_values = {value for value in non_null_values}
            is_numeric = len(numeric_values) == len(non_null_values) and bool(non_null_values)

            payload: dict[str, Any] = {
                "name": column,
                "data_type": "number" if is_numeric else "string",
                "non_null_count": len(non_null_values),
                "null_count": len(values) - len(non_null_values),
                "distinct_count": len(distinct_values),
            }

            if is_numeric:
                payload["min_value"] = min(numeric_values)
                payload["max_value"] = max(numeric_values)
                payload["mean_value"] = statistics.fmean(numeric_values)
            else:
                payload["min_value"] = min(non_null_values) if non_null_values else None
                payload["max_value"] = max(non_null_values) if non_null_values else None

            statistics_payload.append(payload)

        return {"row_count": len(rows), "column_count": len(columns), "columns": statistics_payload}

    @staticmethod
    def _is_number(value: str) -> bool:
        """Check whether a string can be parsed as a floating-point number."""

        try:
            float(value)
            return True
        except ValueError:
            return False
