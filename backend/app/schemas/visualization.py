"""Schemas for dashboards and chart recommendation responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DashboardCreate(BaseModel):
    """Capture the fields needed to create a dashboard container."""

    workspace_id: int
    name: str
    description: str | None = None


class DashboardRead(BaseModel):
    """Expose a dashboard with its persisted creation timestamp."""

    id: int
    workspace_id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardDependencyCreate(BaseModel):
    """Declare a dataset or query execution that powers a dashboard."""

    dataset_id: int
    query_execution_id: int | None = None
    dependency_type: str = "source_dataset"
    details: dict[str, Any] | None = None


class DashboardDependencyRead(BaseModel):
    """Expose a dashboard dependency with parsed metadata details."""

    id: int
    workspace_id: int
    dashboard_id: int
    dataset_id: int
    query_execution_id: int | None
    dependency_type: str
    details: dict[str, Any]
    created_at: datetime


class DashboardKpiOwnerCreate(BaseModel):
    """Assign accountability for a dashboard KPI."""

    kpi_name: str
    owner_email: str
    description: str | None = None


class DashboardKpiOwnerRead(BaseModel):
    """Expose KPI ownership for operational dashboard governance."""

    id: int
    workspace_id: int
    dashboard_id: int
    kpi_name: str
    owner_email: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardImpactItem(BaseModel):
    """One dashboard affected by a dataset dependency."""

    dashboard_id: int
    dashboard_name: str
    dependency_id: int
    dependency_type: str
    query_execution_id: int | None
    kpi_owners: list[DashboardKpiOwnerRead]


class DashboardImpactRead(BaseModel):
    """Describe dashboards that would be affected by a dataset change."""

    workspace_id: int
    dataset_id: int
    impacted_dashboard_count: int
    dashboards: list[DashboardImpactItem]


class ChartRecommendationRequest(BaseModel):
    """Describe the dataset columns and goal for chart selection."""

    dataset_id: int
    x_column: str
    y_column: str | None = None
    goal: str = "compare"


class ChartRecommendationRead(BaseModel):
    """Return the recommended chart type and supporting advice."""

    chart_type: str
    reason: str
    best_practices: list[str]
