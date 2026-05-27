from fastapi import APIRouter

from app.core.observability import observability_store

router = APIRouter()


@router.get("/metrics")
def metrics_snapshot() -> dict[str, object]:
    """Return backend telemetry counters and latency distributions."""

    return observability_store.snapshot()
