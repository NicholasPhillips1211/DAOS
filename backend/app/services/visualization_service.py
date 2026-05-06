from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ChartRecommendation:
    """Recommended chart shape and the rationale behind it."""

    chart_type: str
    reason: str
    best_practices: list[str]


class VisualizationService:
    def recommend_chart(self, x_kind: str, y_kind: str | None, goal: str) -> ChartRecommendation:
        """Choose a chart type from simple data-shape heuristics.

        The MVP favors deterministic chart guidance so the UI can explain why a
        recommendation was made without depending on opaque model behavior.
        """

        goal = goal.lower().strip()
        x_kind = x_kind.lower().strip()
        y_kind = (y_kind or "").lower().strip()

        if x_kind == "datetime" and y_kind == "number":
            return ChartRecommendation(
                chart_type="line",
                reason="Time series data is best read as a trend over time.",
                best_practices=["Keep the time axis ordered", "Avoid dual axes unless absolutely necessary"],
            )

        if x_kind in {"string", "categorical"} and y_kind == "number":
            return ChartRecommendation(
                chart_type="bar",
                reason="Categorical comparisons are clearest in a bar chart.",
                best_practices=["Sort bars by value when comparing ranks", "Limit the number of categories"],
            )

        if x_kind == "number" and y_kind == "number":
            return ChartRecommendation(
                chart_type="scatter",
                reason="Numeric-to-numeric relationships are best shown as a scatter plot.",
                best_practices=["Check for outliers before plotting", "Use transparency for dense point clouds"],
            )

        if goal == "distribution":
            return ChartRecommendation(
                chart_type="histogram",
                reason="Distribution analysis is easiest to understand as a histogram.",
                best_practices=["Use sensible bin widths", "Annotate skew and outliers"],
            )

        return ChartRecommendation(
            chart_type="table",
            reason="The provided structure is not strong enough for a more specialized chart.",
            best_practices=["Prefer clarity over decoration", "Call out any missing values or caveats"],
        )