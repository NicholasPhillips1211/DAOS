from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.metadata import Dataset, Workspace
from app.models.visualization import Dashboard
from app.schemas.visualization import (
    ChartRecommendationRead,
    ChartRecommendationRequest,
    DashboardCreate,
    DashboardRead,
)
from app.services.analytics_service import AnalyticsService
from app.services.visualization_service import VisualizationService

router = APIRouter()
visualization_service = VisualizationService()
analytics_service = AnalyticsService()


@router.get("/dashboards", response_model=list[DashboardRead])
def list_dashboards(db: Session = Depends(get_db)) -> list[Dashboard]:
    """List dashboards newest-first for the workspace overview page."""

    return db.query(Dashboard).order_by(Dashboard.created_at.desc()).all()


@router.post("/dashboards", response_model=DashboardRead, status_code=201)
def create_dashboard(payload: DashboardCreate, db: Session = Depends(get_db)) -> Dashboard:
    """Create a dashboard record as a container for charts and summaries."""

    workspace = db.get(Workspace, payload.workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    dashboard = Dashboard(workspace_id=payload.workspace_id, name=payload.name, description=payload.description)
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard


@router.post("/recommend-chart", response_model=ChartRecommendationRead)
def recommend_chart(payload: ChartRecommendationRequest, db: Session = Depends(get_db)) -> ChartRecommendationRead:
    """Recommend a chart type from the dataset's column shapes and goal."""

    dataset = db.get(Dataset, payload.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if not dataset.storage_path:
        raise HTTPException(status_code=400, detail="Dataset has no storage path")

    try:
        stats = analytics_service.dataset_statistics(dataset.storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found") from None

    stats_map = {column["name"]: column for column in stats["columns"]}
    x_kind = stats_map.get(payload.x_column, {}).get("data_type", "string")
    y_kind = stats_map.get(payload.y_column, {}).get("data_type", None) if payload.y_column else None
    recommendation = visualization_service.recommend_chart(x_kind, y_kind, payload.goal)
    return ChartRecommendationRead(**asdict(recommendation))