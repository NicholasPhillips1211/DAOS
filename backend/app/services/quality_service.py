from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class QualityService:
    def profile_csv(self, file_path: Path) -> dict[str, Any]:
        """Profile a CSV file and return a concise data-quality summary."""

        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        if not rows:
            return {
                "row_count": 0,
                "rejected_rows": 0,
                "quality_score": 100,
                "columns": [],
                "issues": ["Empty dataset"],
            }

        columns = reader.fieldnames or []
        missing_counts = {column: 0 for column in columns}
        blank_rows = 0
        normalized_rows: list[tuple[str, ...]] = []
        column_samples: dict[str, list[str]] = defaultdict(list)

        for row in rows:
            normalized_row: list[str] = []
            row_is_empty = True
            for column in columns:
                value = (row.get(column) or "").strip()
                if value:
                    row_is_empty = False
                else:
                    missing_counts[column] += 1
                column_samples[column].append(value)
                normalized_row.append(value)
            if row_is_empty:
                blank_rows += 1
            normalized_rows.append(tuple(normalized_row))

        duplicate_rows = len(normalized_rows) - len(set(normalized_rows))
        total_cells = max(len(rows) * max(len(columns), 1), 1)
        missing_ratio = sum(missing_counts.values()) / total_cells
        duplicate_ratio = duplicate_rows / max(len(rows), 1)
        blank_ratio = blank_rows / max(len(rows), 1)
        penalty = int((missing_ratio * 50) + (duplicate_ratio * 25) + (blank_ratio * 25))
        quality_score = max(0, min(100, 100 - penalty))

        column_summaries = []
        for column in columns:
            samples = [value for value in column_samples[column] if value]
            inferred_type = self._infer_type(samples)
            column_summaries.append(
                {
                    "name": column,
                    "missing": missing_counts[column],
                    "sample_size": len(samples),
                    "inferred_type": inferred_type,
                }
            )

        issues = []
        if missing_ratio > 0:
            issues.append(f"{sum(missing_counts.values())} missing values detected")
        if duplicate_rows > 0:
            issues.append(f"{duplicate_rows} duplicate rows detected")
        if blank_rows > 0:
            issues.append(f"{blank_rows} fully blank rows detected")

        return {
            "row_count": len(rows),
            "rejected_rows": blank_rows,
            "quality_score": quality_score,
            "columns": column_summaries,
            "issues": issues,
        }

    def render_summary_json(self, summary: dict[str, Any]) -> str:
        """Render a profile summary in stable, human-readable JSON."""

        return json.dumps(summary, indent=2, sort_keys=True)

    def _infer_type(self, values: list[str]) -> str:
        """Infer a column type from the observed sample values."""

        if not values:
            return "string"
        if all(self._is_int(value) for value in values):
            return "integer"
        if all(self._is_number(value) for value in values):
            return "number"
        return "string"

    @staticmethod
    def _is_int(value: str) -> bool:
        """Check whether a string can be losslessly parsed as an integer."""

        try:
            int(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_number(value: str) -> bool:
        """Check whether a string can be parsed as a numeric value."""

        try:
            float(value)
            return True
        except ValueError:
            return False
