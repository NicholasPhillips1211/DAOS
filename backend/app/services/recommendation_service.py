from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.analysis import Insight
from app.models.business import BusinessTranslation
from app.models.metadata import Dataset
from app.models.ml import TrainedModel
from app.models.pipeline import Pipeline
from app.models.recommendation import Recommendation
from app.models.visualization import Dashboard


class RecommendationService:
    def generate_for_workspace(self, db: Session, workspace_id: int) -> list[Recommendation]:
        """Generate action items from the current workspace maturity signals.

        The service intentionally uses simple heuristics so recommendations are
        deterministic, transparent, and easy to test in the MVP.
        """

        db.query(Recommendation).filter(
            Recommendation.workspace_id == workspace_id,
            Recommendation.status == "open",
        ).delete()

        dataset_count = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count()
        pipeline_count = db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).count()
        model_count = db.query(TrainedModel).filter(TrainedModel.workspace_id == workspace_id).count()
        dashboard_count = db.query(Dashboard).filter(Dashboard.workspace_id == workspace_id).count()
        insight_count = db.query(Insight).filter(Insight.workspace_id == workspace_id).count()
        translation_count = db.query(BusinessTranslation).filter(BusinessTranslation.workspace_id == workspace_id).count()

        recommendation_specs: list[dict[str, str]] = []

        if dataset_count == 0:
            recommendation_specs.append(
                {
                    "title": "Ingest your first dataset",
                    "recommendation_type": "ingestion",
                    "priority": "high",
                    "rationale": "No datasets are available, so analytics and ML cannot run.",
                    "action_text": "Use the ingestion endpoint to upload a CSV and create a baseline profile.",
                }
            )

        if dataset_count > 0 and pipeline_count == 0:
            recommendation_specs.append(
                {
                    "title": "Create a repeatable pipeline",
                    "recommendation_type": "pipeline",
                    "priority": "high",
                    "rationale": "Data exists but no pipeline orchestrates repeatable transformations.",
                    "action_text": "Create a pipeline with ingest, quality check, and transform steps.",
                }
            )

        if dataset_count > 0 and model_count == 0:
            recommendation_specs.append(
                {
                    "title": "Train a baseline model",
                    "recommendation_type": "ml",
                    "priority": "medium",
                    "rationale": "You have data but no trained model to generate predictive insights.",
                    "action_text": "Train a first classification or regression model on your highest-value dataset.",
                }
            )

        if dataset_count > 0 and dashboard_count == 0:
            recommendation_specs.append(
                {
                    "title": "Publish an executive dashboard",
                    "recommendation_type": "visualization",
                    "priority": "medium",
                    "rationale": "Dashboards make trends and KPIs visible to stakeholders.",
                    "action_text": "Create a dashboard and add at least one chart recommendation to communicate performance.",
                }
            )

        if insight_count > 0 and translation_count == 0:
            recommendation_specs.append(
                {
                    "title": "Translate insights to business language",
                    "recommendation_type": "business",
                    "priority": "medium",
                    "rationale": "Insights exist but no business framing is stored for decision-makers.",
                    "action_text": "Generate business translations for top insights and share with executives.",
                }
            )

        if not recommendation_specs:
            recommendation_specs.append(
                {
                    "title": "Optimize model and pipeline quality",
                    "recommendation_type": "optimization",
                    "priority": "low",
                    "rationale": "Core capabilities are in place; now focus on quality and operational maturity.",
                    "action_text": "Add monitoring, drift checks, and regular retraining schedules for production readiness.",
                }
            )

        created: list[Recommendation] = []
        for spec in recommendation_specs:
            recommendation = Recommendation(
                workspace_id=workspace_id,
                title=spec["title"],
                recommendation_type=spec["recommendation_type"],
                priority=spec["priority"],
                rationale=spec["rationale"],
                action_text=spec["action_text"],
                status="open",
            )
            db.add(recommendation)
            created.append(recommendation)

        db.commit()
        for recommendation in created:
            db.refresh(recommendation)
        return created
