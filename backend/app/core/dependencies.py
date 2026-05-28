"""Centralized dependency injection for FastAPI routes."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Session:
    """Yield a short-lived database session for request-scoped operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_404(db: Session, model_class, model_id: int, model_name: str = None):
    """Retrieve a model instance or raise a 404 error with a clean message."""
    if model_name is None:
        model_name = model_class.__name__

    instance = db.get(model_class, model_id)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"{model_name} not found")
    return instance


def get_pagination(limit: int = 50, offset: int = 0) -> dict:
    """Provide a small pagination helper for list endpoints.

    - `limit` defaults to 50 and is capped at 1000.
    - `offset` defaults to 0 and must be non-negative.
    """
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be >= 1")
    if limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be <= 1000")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    return {"limit": limit, "offset": offset}
