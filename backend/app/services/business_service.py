from __future__ import annotations

from typing import Tuple

from app.models.analysis import Insight


class BusinessTranslationService:
    def generate(self, insight: Insight, audience: str) -> Tuple[str, str]:
        """Translate a technical insight into business-facing language.

        The MVP uses a deterministic template so the output stays explainable and
        testable before a richer LLM-backed narrator is introduced.
        """

        title = insight.title
        summary = insight.summary
        business_summary = f"For {audience}, '{title}' means: {summary}. Key impact and recommended actions are described below."
        recommendations = '[{"action": "investigate", "reason": "insight requires follow-up"}]'
        return business_summary, recommendations
