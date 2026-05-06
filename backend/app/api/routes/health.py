from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a minimal liveness payload for probes and smoke checks."""

    return {"status": "ok", "service": "daos-backend"}
