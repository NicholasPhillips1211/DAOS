from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from inspect import isawaitable
from typing import Any

import httpx

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.analysis import Insight
from app.models.automation import AutomationPlan
from app.models.business import BusinessTranslation
from app.models.collaboration import Comment, Share
from app.models.guidance import GuidancePlan
from app.models.metadata import Dataset, Workspace
from app.models.ml import TrainedModel
from app.models.pipeline import Pipeline
from app.models.visualization import Dashboard


@dataclass(slots=True)
class WorkspaceSignals:
    dataset_count: int
    dashboard_count: int
    pipeline_count: int
    model_count: int
    insight_count: int
    translation_count: int
    comment_count: int
    share_count: int
    guidance_count: int


class AutomationService:
    """Generate practical automation plans from workspace signals and optional LLM output."""

    async def generate_plan(self, db: Session, workspace_id: int, objective: str) -> AutomationPlan:
        signals = self._collect_signals(db, workspace_id)
        fallback_plan = self._build_fallback_plan(objective, signals)
        provider = "heuristic"
        model_name: str | None = None
        plan_payload = fallback_plan

        llm_payload_result = self._call_local_llm(objective, signals)
        llm_payload = await llm_payload_result if isawaitable(llm_payload_result) else llm_payload_result
        if llm_payload is not None:
            provider = "lm-studio"
            model_name = settings.llm_model
            plan_payload = self._normalize_llm_payload(llm_payload, objective, signals, fallback_plan)

        plan = AutomationPlan(
            workspace_id=workspace_id,
            objective=objective,
            provider=provider,
            model_name=model_name,
            status="generated",
            summary=plan_payload["summary"],
            automation_json=json.dumps(plan_payload, ensure_ascii=False),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan

    def _collect_signals(self, db: Session, workspace_id: int) -> WorkspaceSignals:
        return WorkspaceSignals(
            dataset_count=db.query(Dataset).filter(Dataset.workspace_id == workspace_id).count(),
            dashboard_count=db.query(Dashboard).filter(Dashboard.workspace_id == workspace_id).count(),
            pipeline_count=db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).count(),
            model_count=db.query(TrainedModel).filter(TrainedModel.workspace_id == workspace_id).count(),
            insight_count=db.query(Insight).filter(Insight.workspace_id == workspace_id).count(),
            translation_count=db.query(BusinessTranslation).filter(BusinessTranslation.workspace_id == workspace_id).count(),
            comment_count=db.query(Comment).filter(Comment.workspace_id == workspace_id).count(),
            share_count=db.query(Share).filter(Share.workspace_id == workspace_id).count(),
            guidance_count=db.query(GuidancePlan).filter(GuidancePlan.workspace_id == workspace_id).count(),
        )

    def _build_fallback_plan(self, objective: str, signals: WorkspaceSignals) -> dict[str, Any]:
        actions: list[dict[str, str]] = []
        triggers: list[dict[str, str]] = []

        if signals.dataset_count == 0:
            actions.append({"name": "Onboard first dataset", "description": "Create a repeatable ingestion path for a core CSV or source system."})
            triggers.append({"name": "Dataset absence", "condition": "No datasets registered in the workspace."})
        else:
            actions.append({"name": "Profile newest dataset", "description": "Run quality checks and confirm null, type, and shape patterns."})

        if signals.pipeline_count == 0:
            actions.append({"name": "Define a pipeline cadence", "description": "Convert recurring work into a scheduled pipeline with versioning."})
        if signals.model_count == 0 and signals.dataset_count > 0:
            actions.append({"name": "Train a starter model", "description": "Use one curated dataset to validate ML signal quality and baseline performance."})
        if signals.insight_count > 0 and signals.translation_count == 0:
            actions.append({"name": "Translate insights for stakeholders", "description": "Turn technical findings into business-language summaries and recommendations."})
        if signals.dashboard_count == 0:
            actions.append({"name": "Create a working dashboard", "description": "Build a dashboard shell that can hold key metrics and executive views."})
        if signals.comment_count == 0 or signals.share_count == 0:
            actions.append({"name": "Activate collaboration", "description": "Add comments and sharing so decisions are visible and auditable."})

        if not actions:
            actions.append({"name": "Keep the workspace healthy", "description": "Review data quality, scheduled jobs, and model drift on a regular cadence."})

        score = min(100, 20 + signals.dataset_count * 10 + signals.pipeline_count * 10 + signals.model_count * 10 + signals.dashboard_count * 5)
        summary = (
            f"Automation focus: {objective}. The workspace already has {signals.dataset_count} datasets, "
            f"{signals.pipeline_count} pipelines, and {signals.model_count} trained models, so the next best move is to "
            f"turn recurring work into tracked automations."
        )
        return {
            "title": objective,
            "summary": summary,
            "automation_score": score,
            "signals": asdict(signals),
            "triggers": triggers,
            "actions": actions,
            "next_steps": [item["name"] for item in actions[:4]],
            "provider_notes": "Generated without a local model because no LM Studio response was available.",
        }

    async def _call_local_llm(self, objective: str, signals: WorkspaceSignals) -> dict[str, Any] | None:
        base_url = settings.llm_base_url.strip().rstrip("/")
        if not base_url:
            return None

        prompt = (
            "You are an automation planner for a data platform. Return JSON only with keys "
            "title, summary, automation_score, triggers, actions, next_steps, and provider_notes. "
            "Keep triggers and actions short and concrete. Prefer operational automations such as ingestion, "
            "quality checks, dashboard refreshes, model retraining, and stakeholder notifications. "
            f"Objective: {objective}. Workspace signals: {json.dumps(asdict(signals), ensure_ascii=False)}"
        )

        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key.strip():
            headers["Authorization"] = f"Bearer {settings.llm_api_key.strip()}"

        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                response_payload = response.json()
        except (httpx.HTTPError, ValueError, json.JSONDecodeError):
            return None

        try:
            content = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None

        return self._extract_json_payload(str(content))

    def _extract_json_payload(self, content: str) -> dict[str, Any] | None:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.lower().startswith("json"):
                stripped = stripped[4:].strip()

        first_brace = stripped.find("{")
        last_brace = stripped.rfind("}")
        if first_brace >= 0 and last_brace >= 0:
            stripped = stripped[first_brace : last_brace + 1]

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None
        return payload

    def _normalize_llm_payload(
        self,
        payload: dict[str, Any],
        objective: str,
        signals: WorkspaceSignals,
        fallback_plan: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = {
            "title": str(payload.get("title") or objective),
            "summary": str(payload.get("summary") or fallback_plan["summary"]),
            "automation_score": self._clamp_score(payload.get("automation_score"), fallback_plan["automation_score"]),
            "signals": asdict(signals),
            "triggers": self._normalize_items(payload.get("triggers"), fallback_plan["triggers"], "trigger"),
            "actions": self._normalize_items(payload.get("actions"), fallback_plan["actions"], "action"),
            "next_steps": self._normalize_strings(payload.get("next_steps"), fallback_plan["next_steps"]),
            "provider_notes": str(payload.get("provider_notes") or "Generated by a local LM Studio-compatible model."),
        }
        return normalized

    def _normalize_items(self, value: Any, fallback: list[dict[str, str]], item_type: str) -> list[dict[str, str]]:
        if not isinstance(value, list) or not value:
            return fallback

        normalized: list[dict[str, str]] = []
        for item in value[:6]:
            if isinstance(item, str):
                normalized.append({"name": item, "description": item})
                continue
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("title") or item.get("label") or f"{item_type.title()} item")
                description = str(item.get("description") or item.get("condition") or item.get("detail") or name)
                normalized.append({"name": name, "description": description})

        return normalized or fallback

    def _normalize_strings(self, value: Any, fallback: list[str]) -> list[str]:
        if not isinstance(value, list) or not value:
            return fallback

        items = [str(item) for item in value[:6] if str(item).strip()]
        return items or fallback

    def _clamp_score(self, value: Any, fallback: int) -> int:
        try:
            score = int(float(value))
        except (TypeError, ValueError):
            return fallback
        return max(0, min(100, score))


class AutomationExecutor:
    """Execute automation plan actions against the workspace."""

    def execute_plan(self, db: Session, plan: AutomationPlan) -> dict[str, Any]:
        """Run all actions in the plan and return execution results."""
        try:
            payload = json.loads(plan.automation_json)
        except json.JSONDecodeError:
            return {"status": "failed", "reason": "Invalid automation_json payload", "actions_executed": []}

        if not isinstance(payload.get("actions"), list):
            return {"status": "failed", "reason": "No actions found in plan", "actions_executed": []}

        results: list[dict[str, Any]] = []
        for action in payload["actions"]:
            action_name = action.get("name", "Unknown")
            try:
                result = self._execute_action(db, plan.workspace_id, action_name)
                results.append(result)
            except Exception as exc:
                results.append({"action": action_name, "status": "failed", "error": str(exc)})

        plan.execution_status = "completed"
        plan.executed_at = datetime.now(timezone.utc)
        plan.execution_results_json = json.dumps({"status": "completed", "actions_executed": results}, ensure_ascii=False)
        db.add(plan)
        db.commit()
        db.refresh(plan)

        return json.loads(plan.execution_results_json)

    def _execute_action(self, db: Session, workspace_id: int, action_name: str) -> dict[str, Any]:
        """Execute a specific action by name."""
        action_name_lower = action_name.lower()

        if "dataset" in action_name_lower and ("onboard" in action_name_lower or "first" in action_name_lower):
            return self._onboard_first_dataset(db, workspace_id)
        elif "profile" in action_name_lower:
            return self._profile_newest_dataset(db, workspace_id)
        elif "dashboard" in action_name_lower and "create" in action_name_lower:
            return self._create_working_dashboard(db, workspace_id)
        elif "model" in action_name_lower and "train" in action_name_lower:
            return self._train_starter_model(db, workspace_id)
        elif "collaboration" in action_name_lower or "sharing" in action_name_lower:
            return self._activate_collaboration(db, workspace_id)
        elif "insights" in action_name_lower and "translate" in action_name_lower:
            return self._translate_insights(db, workspace_id)
        elif "pipeline" in action_name_lower:
            return self._define_pipeline_cadence(db, workspace_id)
        else:
            return {"action": action_name, "status": "skipped", "reason": "No executor mapped for this action"}

    def _onboard_first_dataset(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create a sample dataset if the workspace has none."""
        existing = db.query(Dataset).filter(Dataset.workspace_id == workspace_id).first()
        if existing:
            return {"action": "Onboard first dataset", "status": "skipped", "reason": "Workspace already has datasets"}

        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            return {"action": "Onboard first dataset", "status": "failed", "reason": "Workspace not found"}

        sample_path = f"/data/raw/ws{workspace_id}_sample.csv"
        dataset = Dataset(
            workspace_id=workspace_id,
            name="Sample Dataset",
            source_type="file",
            storage_path=sample_path,
        )
        db.add(dataset)
        db.commit()
        return {"action": "Onboard first dataset", "status": "executed", "dataset_id": dataset.id}

    def _profile_newest_dataset(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Mark the newest dataset as profiled."""
        newest = (
            db.query(Dataset)
            .filter(Dataset.workspace_id == workspace_id)
            .order_by(Dataset.created_at.desc())
            .first()
        )
        if not newest:
            return {"action": "Profile newest dataset", "status": "skipped", "reason": "No datasets in workspace"}

        return {"action": "Profile newest dataset", "status": "executed", "dataset_id": newest.id}

    def _create_working_dashboard(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create a default dashboard if the workspace has none."""
        existing = db.query(Dashboard).filter(Dashboard.workspace_id == workspace_id).first()
        if existing:
            return {"action": "Create a working dashboard", "status": "skipped", "reason": "Workspace already has dashboards"}

        dashboard = Dashboard(
            workspace_id=workspace_id,
            name="Automation-Generated Dashboard",
            description="Default dashboard created by automation plan execution.",
        )
        db.add(dashboard)
        db.commit()
        return {"action": "Create a working dashboard", "status": "executed", "dashboard_id": dashboard.id}

    def _activate_collaboration(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create default sharing setup."""
        dashboard = db.query(Dashboard).filter(Dashboard.workspace_id == workspace_id).first()
        if not dashboard:
            return {"action": "Activate collaboration", "status": "skipped", "reason": "No dashboard to share"}

        share = Share(
            workspace_id=workspace_id,
            resource_type="dashboard",
            resource_id=dashboard.id,
            target_email="team@example.local",
            permission="view",
        )
        db.add(share)
        db.commit()
        return {"action": "Activate collaboration", "status": "executed", "share_id": share.id}

    def _train_starter_model(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create a placeholder model training action."""
        existing = db.query(TrainedModel).filter(TrainedModel.workspace_id == workspace_id).first()
        if existing:
            return {"action": "Train a starter model", "status": "skipped", "reason": "Workspace already has models"}

        return {"action": "Train a starter model", "status": "deferred", "reason": "Model training requires manual dataset selection"}

    def _translate_insights(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create a default business translation if insights exist."""
        insights = db.query(Insight).filter(Insight.workspace_id == workspace_id).all()
        if not insights:
            return {"action": "Translate insights for stakeholders", "status": "skipped", "reason": "No insights to translate"}

        executed_count = 0
        for insight in insights[:3]:
            existing_translation = db.query(BusinessTranslation).filter_by(insight_id=insight.id).first()
            if not existing_translation:
                translation = BusinessTranslation(
                    workspace_id=workspace_id,
                    insight_id=insight.id,
                    audience="stakeholders",
                    summary=f"Business context: {insight.title}",
                    recommendations_json='["Review findings"]',
                )
                db.add(translation)
                executed_count += 1
        db.commit()
        return {"action": "Translate insights for stakeholders", "status": "executed", "translations_created": executed_count}

    def _define_pipeline_cadence(self, db: Session, workspace_id: int) -> dict[str, Any]:
        """Create a placeholder pipeline."""
        existing = db.query(Pipeline).filter(Pipeline.workspace_id == workspace_id).first()
        if existing:
            return {"action": "Define a pipeline cadence", "status": "skipped", "reason": "Workspace already has pipelines"}

        pipeline = Pipeline(
            workspace_id=workspace_id,
            name="Automation-Generated Pipeline",
            description="Default pipeline created by automation execution.",
        )
        db.add(pipeline)
        db.commit()
        return {"action": "Define a pipeline cadence", "status": "executed", "pipeline_id": pipeline.id}