from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb


CLEANING_POLICY = {
    "id": "duckdb_csv_cleaning_v1",
    "version": "1.0",
    "engine": "duckdb",
    "rules": [
        "preserve_raw_file",
        "normalize_headers",
        "trim_whitespace",
        "drop_blank_rows",
        "deduplicate_rows",
        "quarantine_rejected_rows",
    ],
}


@dataclass(frozen=True, slots=True)
class CsvShape:
    headers: list[str]
    raw_header_count: int
    column_count: int
    short_rows_padded: int
    extra_columns_preserved: int


class QualityService:
    def clean_csv(self, raw_path: Path, cleaned_path: Path, rejected_path: Path) -> dict[str, Any]:
        """Write governed cleaned/rejected CSV artifacts while preserving the raw file."""

        cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        rejected_path.parent.mkdir(parents=True, exist_ok=True)

        # DuckDB needs a fixed column map before scanning ragged CSVs. This
        # lightweight stream pass discovers shape only; row transformation,
        # rejection, and counting stay inside DuckDB for scale.
        shape = self._inspect_csv(raw_path)
        policy_fingerprint = self._json_fingerprint(CLEANING_POLICY)

        if shape.column_count == 0:
            with cleaned_path.open("w", newline="", encoding="utf-8"):
                pass
            with rejected_path.open("w", newline="", encoding="utf-8"):
                pass
            return {
                "raw_row_count": 0,
                "cleaned_row_count": 0,
                "blank_rows_removed": 0,
                "duplicate_rows_removed": 0,
                "cells_trimmed": 0,
                "extra_columns_preserved": 0,
                "short_rows_padded": 0,
                "rejected_row_count": 0,
                "headers_normalized": [],
                "engine": CLEANING_POLICY["engine"],
                "policy": CLEANING_POLICY,
                "policy_fingerprint": policy_fingerprint,
                "rules": CLEANING_POLICY["rules"],
                "cleaned_path": str(cleaned_path),
                "rejected_path": str(rejected_path),
                "artifact_fingerprints": {
                    "raw": self._file_fingerprint(raw_path),
                    "cleaned": self._file_fingerprint(cleaned_path),
                    "rejected": self._file_fingerprint(rejected_path),
                    "policy": policy_fingerprint,
                },
            }

        cleaned_headers, headers_normalized = self._normalize_headers(shape.headers)
        raw_scan = self._duckdb_read_csv(raw_path, shape.column_count)
        blank_predicate = self._blank_predicate(cleaned_headers)
        cleaned_columns = ", ".join(self._quote_identifier(header) for header in cleaned_headers)
        cleaned_select = ", ".join(f"trim(coalesce(raw_{index}, '')) AS {self._quote_identifier(header)}" for index, header in enumerate(cleaned_headers))
        trim_counter = " + ".join(
            f"CASE WHEN coalesce(raw_{index}, '') <> trim(coalesce(raw_{index}, '')) THEN 1 ELSE 0 END"
            for index in range(shape.column_count)
        )

        with duckdb.connect(database=":memory:") as conn:
            # Accepted and rejected artifacts are derived from the same
            # classified table so counts, row order, and quarantine reasons
            # cannot drift between separate code paths.
            conn.execute(
                f"""
                CREATE TEMP TABLE classified_cleaning AS
                WITH source_rows AS (
                    SELECT row_number() OVER () AS source_row_number, *
                    FROM {raw_scan}
                ),
                prepared AS (
                    SELECT
                        source_row_number,
                        {cleaned_select},
                        {trim_counter} AS cells_trimmed
                    FROM source_rows
                    WHERE source_row_number > 1
                )
                SELECT
                    prepared.*,
                    ({blank_predicate}) AS is_blank,
                    row_number() OVER (PARTITION BY {cleaned_columns} ORDER BY source_row_number) AS duplicate_rank
                FROM prepared
                """
            )
            counts = conn.execute(
                """
                SELECT
                    count(*) AS raw_row_count,
                    coalesce(sum(CASE WHEN is_blank THEN 1 ELSE 0 END), 0) AS blank_rows_removed,
                    coalesce(sum(CASE WHEN NOT is_blank AND duplicate_rank > 1 THEN 1 ELSE 0 END), 0) AS duplicate_rows_removed,
                    coalesce(sum(cells_trimmed), 0) AS cells_trimmed
                FROM classified_cleaning
                """
            ).fetchone()
            self._copy_query_to_csv(
                conn,
                f"""
                SELECT {cleaned_columns}
                FROM classified_cleaning
                WHERE NOT is_blank AND duplicate_rank = 1
                ORDER BY source_row_number
                """,
                cleaned_path,
            )
            self._copy_query_to_csv(
                conn,
                f"""
                SELECT
                    source_row_number,
                    CASE WHEN is_blank THEN 'blank_row' ELSE 'duplicate_row' END AS rejection_reason,
                    {cleaned_columns}
                FROM classified_cleaning
                WHERE is_blank OR duplicate_rank > 1
                ORDER BY source_row_number
                """,
                rejected_path,
            )

        raw_row_count = int(counts[0] or 0)
        blank_rows_removed = int(counts[1] or 0)
        duplicate_rows_removed = int(counts[2] or 0)
        cells_trimmed = int(counts[3] or 0)
        rejected_row_count = blank_rows_removed + duplicate_rows_removed
        cleaned_row_count = max(raw_row_count - rejected_row_count, 0)

        return {
            "raw_row_count": raw_row_count,
            "cleaned_row_count": cleaned_row_count,
            "blank_rows_removed": blank_rows_removed,
            "duplicate_rows_removed": duplicate_rows_removed,
            "cells_trimmed": cells_trimmed,
            "extra_columns_preserved": shape.extra_columns_preserved,
            "short_rows_padded": shape.short_rows_padded,
            "rejected_row_count": rejected_row_count,
            "headers_normalized": headers_normalized,
            "engine": CLEANING_POLICY["engine"],
            "policy": CLEANING_POLICY,
            "policy_fingerprint": policy_fingerprint,
            "rules": CLEANING_POLICY["rules"],
            "cleaned_path": str(cleaned_path),
            "rejected_path": str(rejected_path),
            "artifact_fingerprints": {
                "raw": self._file_fingerprint(raw_path),
                "cleaned": self._file_fingerprint(cleaned_path),
                "rejected": self._file_fingerprint(rejected_path),
                "policy": policy_fingerprint,
            },
        }

    def profile_csv(self, file_path: Path) -> dict[str, Any]:
        """Profile a CSV file with DuckDB and return a concise data-quality summary."""

        shape = self._inspect_csv(file_path)
        if shape.column_count == 0:
            return {
                "row_count": 0,
                "rejected_rows": 0,
                "quality_score": 100,
                "columns": [],
                "issues": ["Empty dataset"],
            }

        columns, _ = self._normalize_headers(shape.headers)
        raw_scan = self._duckdb_read_csv(file_path, shape.column_count)
        cleaned_select = ", ".join(f"trim(coalesce(raw_{index}, '')) AS {self._quote_identifier(column)}" for index, column in enumerate(columns))
        blank_predicate = self._blank_predicate(columns)
        profile_columns = ", ".join(self._quote_identifier(column) for column in columns)

        with duckdb.connect(database=":memory:") as conn:
            # Profile from VARCHAR values first. Badly typed input should become
            # visible quality evidence instead of failing ingestion before the
            # analyst can inspect and remediate it.
            conn.execute(
                f"""
                CREATE TEMP TABLE profile_rows AS
                WITH source_rows AS (
                    SELECT row_number() OVER () AS source_row_number, *
                    FROM {raw_scan}
                )
                SELECT {cleaned_select}
                FROM source_rows
                WHERE source_row_number > 1
                """
            )
            row_count = int(conn.execute("SELECT count(*) FROM profile_rows").fetchone()[0] or 0)

            if row_count == 0:
                return {
                    "row_count": 0,
                    "rejected_rows": 0,
                    "quality_score": 100,
                    "columns": [
                        {
                            "name": column,
                            "missing": 0,
                            "sample_size": 0,
                            "inferred_type": "string",
                        }
                        for column in columns
                    ],
                    "issues": ["Empty dataset"],
                }

            blank_rows = int(conn.execute(f"SELECT count(*) FROM profile_rows WHERE {blank_predicate}").fetchone()[0] or 0)
            distinct_rows = int(conn.execute(f"SELECT count(*) FROM (SELECT DISTINCT {profile_columns} FROM profile_rows)").fetchone()[0] or 0)
            duplicate_rows = max(row_count - distinct_rows, 0)
            column_summaries = []
            total_missing = 0
            for column in columns:
                quoted_column = self._quote_identifier(column)
                missing, sample_size, int_count, number_count = conn.execute(
                    f"""
                    SELECT
                        coalesce(sum(CASE WHEN {quoted_column} = '' THEN 1 ELSE 0 END), 0) AS missing,
                        coalesce(sum(CASE WHEN {quoted_column} <> '' THEN 1 ELSE 0 END), 0) AS sample_size,
                        coalesce(sum(CASE WHEN {quoted_column} <> '' AND regexp_full_match({quoted_column}, '^[+-]?[0-9]+$') THEN 1 ELSE 0 END), 0) AS int_count,
                        coalesce(sum(CASE WHEN {quoted_column} <> '' AND try_cast({quoted_column} AS DOUBLE) IS NOT NULL THEN 1 ELSE 0 END), 0) AS number_count
                    FROM profile_rows
                    """
                ).fetchone()
                missing = int(missing or 0)
                sample_size = int(sample_size or 0)
                total_missing += missing
                column_summaries.append(
                    {
                        "name": column,
                        "missing": missing,
                        "sample_size": sample_size,
                        "inferred_type": self._infer_type_from_counts(sample_size, int(int_count or 0), int(number_count or 0)),
                    }
                )

        total_cells = max(row_count * max(len(columns), 1), 1)
        missing_ratio = total_missing / total_cells
        duplicate_ratio = duplicate_rows / max(row_count, 1)
        blank_ratio = blank_rows / max(row_count, 1)
        penalty = int((missing_ratio * 50) + (duplicate_ratio * 25) + (blank_ratio * 25))
        quality_score = max(0, min(100, 100 - penalty))

        issues = []
        if missing_ratio > 0:
            issues.append(f"{total_missing} missing values detected")
        if duplicate_rows > 0:
            issues.append(f"{duplicate_rows} duplicate rows detected")
        if blank_rows > 0:
            issues.append(f"{blank_rows} fully blank rows detected")

        return {
            "row_count": row_count,
            "rejected_rows": blank_rows,
            "quality_score": quality_score,
            "columns": column_summaries,
            "issues": issues,
        }

    def compare_profiles(self, raw_profile: dict[str, Any], cleaned_profile: dict[str, Any], cleaning_summary: dict[str, Any]) -> dict[str, Any]:
        """Summarize quality movement from raw input to cleaned analytical artifact."""

        raw_score = int(raw_profile.get("quality_score", 0) or 0)
        cleaned_score = int(cleaned_profile.get("quality_score", 0) or 0)
        return {
            "raw_quality_score": raw_score,
            "cleaned_quality_score": cleaned_score,
            "score_delta": cleaned_score - raw_score,
            "raw_row_count": raw_profile.get("row_count", 0),
            "cleaned_row_count": cleaned_profile.get("row_count", 0),
            "rejected_row_count": cleaning_summary.get("rejected_row_count", 0),
            "blank_rows_removed": cleaning_summary.get("blank_rows_removed", 0),
            "duplicate_rows_removed": cleaning_summary.get("duplicate_rows_removed", 0),
        }

    def render_summary_json(self, summary: dict[str, Any]) -> str:
        """Render a profile summary in stable, human-readable JSON."""

        return json.dumps(summary, indent=2, sort_keys=True)

    def _inspect_csv(self, file_path: Path) -> CsvShape:
        """Stream a CSV once to discover its logical shape for DuckDB reads."""

        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            try:
                headers = next(reader)
            except StopIteration:
                return CsvShape(headers=[], raw_header_count=0, column_count=0, short_rows_padded=0, extra_columns_preserved=0)

            raw_header_count = len(headers)
            column_count = raw_header_count
            row_width_counts: dict[int, int] = {}
            for row in reader:
                row_width = len(row)
                row_width_counts[row_width] = row_width_counts.get(row_width, 0) + 1
                column_count = max(column_count, row_width)

        padded_headers = [*headers, *[""] * max(column_count - raw_header_count, 0)]
        short_rows_padded = sum(count for width, count in row_width_counts.items() if width < column_count)
        return CsvShape(
            headers=padded_headers,
            raw_header_count=raw_header_count,
            column_count=column_count,
            short_rows_padded=short_rows_padded,
            extra_columns_preserved=max(column_count - raw_header_count, 0),
        )

    def _duckdb_read_csv(self, file_path: Path, column_count: int) -> str:
        """Build a tolerant DuckDB CSV scan for analyst-supplied files."""

        columns = ", ".join(f"'raw_{index}':'VARCHAR'" for index in range(column_count))
        return (
            f"read_csv('{self._escape_sql_string(str(file_path))}', "
            "header=false, all_varchar=true, null_padding=true, "
            "ignore_errors=true, strict_mode=false, "
            f"columns={{{columns}}})"
        )

    def _copy_query_to_csv(self, conn: duckdb.DuckDBPyConnection, query: str, target_path: Path) -> None:
        conn.execute(f"COPY ({query}) TO '{self._escape_sql_string(str(target_path))}' (HEADER, DELIMITER ',')")

    @staticmethod
    def _blank_predicate(columns: list[str]) -> str:
        return " AND ".join(f"{QualityService._quote_identifier(column)} = ''" for column in columns) or "true"

    @staticmethod
    def _infer_type_from_counts(sample_size: int, int_count: int, number_count: int) -> str:
        if sample_size == 0:
            return "string"
        if int_count == sample_size:
            return "integer"
        if number_count == sample_size:
            return "number"
        return "string"

    @staticmethod
    def _quote_identifier(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    @staticmethod
    def _escape_sql_string(value: str) -> str:
        return value.replace("'", "''")

    @staticmethod
    def _file_fingerprint(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _json_fingerprint(payload: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_headers(headers: list[str]) -> tuple[list[str], list[dict[str, str]]]:
        normalized: list[str] = []
        changes: list[dict[str, str]] = []
        seen: dict[str, int] = {}

        for index, header in enumerate(headers):
            base = re.sub(r"[^0-9a-zA-Z]+", "_", header.strip().lower()).strip("_")
            if not base:
                base = f"column_{index + 1}"
            if base[0].isdigit():
                base = f"column_{index + 1}_{base}"
            candidate = base
            seen_count = seen.get(base, 0)
            if seen_count:
                candidate = f"{base}_{seen_count + 1}"
            seen[base] = seen_count + 1
            normalized.append(candidate)
            if candidate != header:
                changes.append({"from": header, "to": candidate})

        return normalized, changes
