from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.auth import Principal, WORKSPACE_READ_ROLES, get_current_principal, require_workspace_role
from app.core.dependencies import get_db
from app.core.dependencies import get_pagination
from app.schemas.metadata import (
    AIContextBuildRequest,
    AIContextBuildResponse,
    MetadataAIContextRecordRead,
    MetadataEventRead,
    MetadataLineageRecordRead,
    MetadataOwnershipRecordRead,
    MetadataSchemaRecordRead,
    MetadataUsageEventRead,
)
from app.services.ai_context_builder_service import AIContextBuilderService
from app.services.metadata_service import MetadataService

router = APIRouter()
metadata_service = MetadataService()
ai_context_builder_service = AIContextBuilderService(metadata_service)


@router.get("/events", response_model=list[MetadataEventRead])
def list_metadata_events(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for metadata retrieval"),
    event_type: str | None = Query(default=None, description="Exact event type filter"),
    resource_type: str | None = Query(default=None, description="Resource type filter"),
    resource_id: int | None = Query(default=None, description="Resource id filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataEventRead]:
    """Expose queryable metadata events for lineage and workflow intelligence."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_events(db, workspace_id=workspace_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id)
    response.headers["X-Total-Count"] = str(total)

    events = metadata_service.list_events(
        db,
        workspace_id=workspace_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=pagination["limit"],
    )

    return [
        MetadataEventRead(
            id=event.id,
            workspace_id=event.workspace_id,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            actor=event.actor,
            details=metadata_service.parse_details(event),
            created_at=event.created_at,
        )
        for event in events
    ]


@router.get("/schemas", response_model=list[MetadataSchemaRecordRead])
def list_metadata_schemas(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for schema retrieval"),
    asset_type: str | None = Query(default=None, description="Asset type filter"),
    asset_id: int | None = Query(default=None, description="Asset id filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataSchemaRecordRead]:
    """Expose schema snapshots for governed information assets."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_schema_records(db, workspace_id=workspace_id, asset_type=asset_type, asset_id=asset_id)
    response.headers["X-Total-Count"] = str(total)
    records = metadata_service.list_schema_records(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [
        MetadataSchemaRecordRead(
            id=record.id,
            workspace_id=record.workspace_id,
            asset_type=record.asset_type,
            asset_id=record.asset_id,
            schema=metadata_service.parse_record_json(record.schema_json),
            profile_fingerprint=record.profile_fingerprint,
            source=record.source,
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get("/lineage", response_model=list[MetadataLineageRecordRead])
def list_metadata_lineage(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for lineage retrieval"),
    asset_type: str | None = Query(default=None, description="Asset type participating in lineage"),
    asset_id: int | None = Query(default=None, description="Asset id participating in lineage"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataLineageRecordRead]:
    """Expose dependency edges between lifecycle assets."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_lineage_records(db, workspace_id=workspace_id, asset_type=asset_type, asset_id=asset_id)
    response.headers["X-Total-Count"] = str(total)
    records = metadata_service.list_lineage_records(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [
        MetadataLineageRecordRead(
            id=record.id,
            workspace_id=record.workspace_id,
            upstream_type=record.upstream_type,
            upstream_id=record.upstream_id,
            downstream_type=record.downstream_type,
            downstream_id=record.downstream_id,
            relation_type=record.relation_type,
            details=metadata_service.parse_record_json(record.details_json),
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get("/usage", response_model=list[MetadataUsageEventRead])
def list_metadata_usage(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for usage retrieval"),
    asset_type: str | None = Query(default=None, description="Asset type filter"),
    asset_id: int | None = Query(default=None, description="Asset id filter"),
    action: str | None = Query(default=None, description="Exact usage action filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataUsageEventRead]:
    """Expose usage events that show how governed information is consumed."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_usage_events(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        action=action,
    )
    response.headers["X-Total-Count"] = str(total)
    records = metadata_service.list_usage_events(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        action=action,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [
        MetadataUsageEventRead(
            id=record.id,
            workspace_id=record.workspace_id,
            asset_type=record.asset_type,
            asset_id=record.asset_id,
            action=record.action,
            actor=record.actor,
            details=metadata_service.parse_record_json(record.details_json),
            created_at=record.created_at,
        )
        for record in records
    ]


@router.get("/ownership", response_model=list[MetadataOwnershipRecordRead])
def list_metadata_ownership(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for ownership retrieval"),
    asset_type: str | None = Query(default=None, description="Asset type filter"),
    asset_id: int | None = Query(default=None, description="Asset id filter"),
    owner_email: str | None = Query(default=None, description="Owner email filter"),
    steward_email: str | None = Query(default=None, description="Steward email filter"),
    stewardship_status: str | None = Query(default=None, description="Stewardship status filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataOwnershipRecordRead]:
    """Expose ownership and stewardship metadata for governed information assets."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_ownership_records(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        owner_email=owner_email,
        steward_email=steward_email,
        stewardship_status=stewardship_status,
    )
    response.headers["X-Total-Count"] = str(total)
    records = metadata_service.list_ownership_records(
        db,
        workspace_id=workspace_id,
        asset_type=asset_type,
        asset_id=asset_id,
        owner_email=owner_email,
        steward_email=steward_email,
        stewardship_status=stewardship_status,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [
        MetadataOwnershipRecordRead(
            id=record.id,
            workspace_id=record.workspace_id,
            asset_type=record.asset_type,
            asset_id=record.asset_id,
            owner_email=record.owner_email,
            steward_email=record.steward_email,
            stewardship_status=record.stewardship_status,
            details=metadata_service.parse_record_json(record.details_json),
            created_at=record.created_at,
        )
        for record in records
    ]


@router.post("/ai-context/build", response_model=AIContextBuildResponse, status_code=201)
def build_metadata_ai_context(
    payload: AIContextBuildRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
) -> AIContextBuildResponse:
    """Build and persist a reusable AI grounding snapshot for a workspace.

    The route only validates access and formats the response; lifecycle evidence
    gathering lives in `AIContextBuilderService` so other AI features can reuse
    the same modular context builder.
    """

    require_workspace_role(db, payload.workspace_id, principal, WORKSPACE_READ_ROLES)
    result = ai_context_builder_service.build_workspace_context(
        db,
        workspace_id=payload.workspace_id,
        objective=payload.objective,
        actor=principal.user_email,
    )
    return AIContextBuildResponse(
        id=result.record.id,
        workspace_id=result.record.workspace_id,
        context_type=result.record.context_type,
        resource_type=result.record.resource_type,
        resource_id=result.record.resource_id,
        actor=result.record.actor,
        objective=result.context.get("objective"),
        summary=result.context["summary"],
        confidence_score=result.context["confidence_score"],
        sources=result.context["sources"],
        recommended_next_actions=result.context["recommended_next_actions"],
        context=result.context,
        created_at=result.record.created_at,
    )


@router.get("/ai-context", response_model=list[MetadataAIContextRecordRead])
def list_metadata_ai_context(
    response: Response,
    workspace_id: int = Query(..., description="Workspace scope for AI context retrieval"),
    context_type: str | None = Query(default=None, description="AI context type filter"),
    resource_type: str | None = Query(default=None, description="Grounded resource type filter"),
    resource_id: int | None = Query(default=None, description="Grounded resource id filter"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
    pagination: dict = Depends(get_pagination),
) -> list[MetadataAIContextRecordRead]:
    """Expose AI grounding snapshots generated from lifecycle metadata."""

    require_workspace_role(db, workspace_id, principal, WORKSPACE_READ_ROLES)
    total = metadata_service.count_ai_context_records(
        db,
        workspace_id=workspace_id,
        context_type=context_type,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    response.headers["X-Total-Count"] = str(total)
    records = metadata_service.list_ai_context_records(
        db,
        workspace_id=workspace_id,
        context_type=context_type,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    return [
        MetadataAIContextRecordRead(
            id=record.id,
            workspace_id=record.workspace_id,
            context_type=record.context_type,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            actor=record.actor,
            context=metadata_service.parse_record_json(record.context_json),
            created_at=record.created_at,
        )
        for record in records
    ]
