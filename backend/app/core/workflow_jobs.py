"""Canonical work-item names shared by API producers and worker consumers."""

from __future__ import annotations


INGESTION_CLEAN_PROFILE_JOB = "ingestion.clean_profile"
LEGACY_INGESTION_PROFILE_JOB = "ingestion.profile"

INGESTION_CLEAN_PROFILE_JOB_TYPES = frozenset(
    {
        INGESTION_CLEAN_PROFILE_JOB,
        LEGACY_INGESTION_PROFILE_JOB,
    }
)


def expand_work_job_types(job_types: set[str] | None) -> set[str] | None:
    """Expand canonical work-type filters to include compatible legacy names."""

    if job_types is None:
        return None

    expanded = set(job_types)
    if expanded & INGESTION_CLEAN_PROFILE_JOB_TYPES:
        expanded.update(INGESTION_CLEAN_PROFILE_JOB_TYPES)
    return expanded
