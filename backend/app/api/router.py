from fastapi import APIRouter

from app.api.routes import analytics, automation, business, collaboration, datasets, guidance, governance, health, ingestion, lakehouse, ml, observability, pipelines, quality, recommendations, visualization, workspaces, metadata

api_router = APIRouter()

# Route registry: (module, prefix, tags)
ROUTES = [
    (health, "", ["health"]),
    (workspaces, "/workspaces", ["workspaces"]),
    (datasets, "/datasets", ["datasets"]),
    (ingestion, "/ingestion", ["ingestion"]),
    (observability, "/observability", ["observability"]),
    (lakehouse, "/lakehouse", ["lakehouse"]),
    (quality, "/datasets", ["quality"]),
    (pipelines, "/pipelines", ["pipelines"]),
    (ml, "/ml", ["ml"]),
    (visualization, "/visualizations", ["visualizations"]),
    (analytics, "/analytics", ["analytics"]),
    (metadata, "/metadata", ["metadata"]),
    (automation, "/automation", ["automation"]),
    (collaboration, "/collaboration", ["collaboration"]),
    (governance, "/governance", ["governance"]),
    (business, "/business", ["business"]),
    (recommendations, "/recommendations", ["recommendations"]),
    (guidance, "/guidance", ["guidance"]),
]

for module, prefix, tags in ROUTES:
    api_router.include_router(module.router, prefix=prefix, tags=tags)
