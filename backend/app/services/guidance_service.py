from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.analysis import Insight
from app.models.business import BusinessTranslation
from app.models.guidance import GuidancePlan
from app.models.metadata import Dataset
from app.models.ml import TrainedModel
from app.models.pipeline import Pipeline


class GuidanceService:
    def generate_plan(self, db: Session, workspace_id: int, objective: str) -> GuidancePlan:
        """Generate a lightweight execution plan from the workspace's maturity signals.

        The plan combines current counts with fixed milestones so teams get an
        actionable next-step framework without needing a heavyweight planning engine.
        """

        dataset_count = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count()
        pipeline_count = db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).count()
        model_count = db.query(TrainedModel).filter(TrainedModel.workspace_id == workspace_id).count()
        insight_count = db.query(Insight).filter(Insight.workspace_id == workspace_id).count()
        translation_count = db.query(BusinessTranslation).filter(BusinessTranslation.workspace_id == workspace_id).count()

        kpis = [
            {"name": "Data readiness", "target": "95% datasets profiled", "current": f"{dataset_count} datasets"},
            {"name": "Pipeline automation", "target": "Daily scheduled flows", "current": f"{pipeline_count} pipelines"},
            {"name": "Model adoption", "target": "At least 1 production model", "current": f"{model_count} models"},
        ]

        milestones = [
            {"phase": "30 days", "goal": "Stabilize ingestion and data quality"},
            {"phase": "60 days", "goal": "Operationalize analytics and pipelines"},
            {"phase": "90 days", "goal": "Scale ML and business narrative distribution"},
        ]

        risks = []
        if dataset_count == 0:
            risks.append({"risk": "No source data", "mitigation": "Prioritize onboarding at least one core dataset"})
        if pipeline_count == 0:
            risks.append({"risk": "Manual workflows", "mitigation": "Create repeatable pipeline definitions and schedules"})
        if insight_count > 0 and translation_count == 0:
            risks.append({"risk": "Insight-to-action gap", "mitigation": "Generate business translations for key insights"})
        if not risks:
            risks.append({"risk": "Operational drift", "mitigation": "Monitor data quality and model performance continuously"})

        plan = GuidancePlan(
            workspace_id=workspace_id,
            objective=objective,
            kpis_json=json.dumps(kpis),
            milestones_json=json.dumps(milestones),
            risks_json=json.dumps(risks),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
