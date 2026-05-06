from dataclasses import dataclass


@dataclass(slots=True)
class IngestionResult:
    """Outcome of a batch ingestion run."""

    dataset_id: int
    raw_rows: int
    rejected_rows: int
    quality_score: float


class IngestionService:
    def infer_source_type(self, source_name: str) -> str:
        """Infer a coarse source category from the provided name or URL.

        The heuristic is intentionally simple because the ingestion MVP only needs
        to route uploads into a few well-understood source buckets.
        """

        if source_name.endswith((".csv", ".tsv")):
            return "file"
        if source_name.startswith("http"):
            return "api"
        return "database"
