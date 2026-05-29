from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import accuracy_score, r2_score


class MLService:
    def _load_csv_rows(self, file_path: str | Path) -> list[dict[str, Any]]:
        """Load CSV rows into dictionaries so scikit-learn can consume them."""

        dataset_path = Path(file_path)
        with dataset_path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))

    def train_model(self, file_path: str | Path, target_column: str, task_type: str, artifact_path: str | Path) -> dict[str, Any]:
        """Train a small tree-based model and persist the fitted artifact.

        This keeps the MVP explainable and fast to iterate on while still
        producing metrics, feature importances, and an artifact for reuse.
        """

        rows = self._load_csv_rows(file_path)
        if not rows:
            raise ValueError("Dataset is empty")

        if target_column not in rows[0]:
            raise ValueError(f"Target column '{target_column}' was not found")

        features: list[dict[str, Any]] = []
        targets: list[Any] = []
        for row in rows:
            target_value = (row.get(target_column) or "").strip()
            if target_value == "":
                continue
            feature_row: dict[str, Any] = {}
            for column, value in row.items():
                if column == target_column:
                    continue
                cleaned_value = (value or "").strip()
                feature_row[column] = self._coerce_value(cleaned_value)
            features.append(feature_row)
            targets.append(self._coerce_target(target_value, task_type))

        if len(features) < 2:
            raise ValueError("Need at least two labeled rows to train a model")

        vectorizer = DictVectorizer(sparse=False)
        matrix = vectorizer.fit_transform(features)
        x_train, x_test, y_train, y_test = train_test_split(matrix, targets, test_size=0.33, random_state=42)

        if task_type == "regression":
            model = DecisionTreeRegressor(random_state=42)
        else:
            model = DecisionTreeClassifier(random_state=42)

        model.fit(x_train, y_train)
        train_score = model.score(x_train, y_train)
        test_score = model.score(x_test, y_test)
        overfit_detected = train_score - test_score > 0.15

        if task_type == "regression":
            predictions = model.predict(x_test)
            metric_name = "r2"
            metric_value = r2_score(y_test, predictions)
        else:
            predictions = model.predict(x_test)
            metric_name = "accuracy"
            metric_value = accuracy_score(y_test, predictions)

        artifact_path = Path(artifact_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "vectorizer": vectorizer}, artifact_path)

        importances = []
        if hasattr(model, "feature_importances_"):
            feature_names = vectorizer.get_feature_names_out()
            importances = sorted(
                (
                    {"feature": feature, "importance": float(importance)}
                    for feature, importance in zip(feature_names, model.feature_importances_, strict=False)
                    if float(importance) > 0
                ),
                key=lambda item: item["importance"],
                reverse=True,
            )

        return {
            "model_type": model.__class__.__name__,
            "metric_name": metric_name,
            "metric_value": float(metric_value),
            "train_score": float(train_score),
            "test_score": float(test_score),
            "overfit_detected": overfit_detected,
            "artifact_path": str(artifact_path),
            "feature_importances": importances,
        }

    @staticmethod
    def _coerce_value(value: str) -> Any:
        """Convert numeric-looking feature values so the model can use them."""

        if value == "":
            return ""
        try:
            return float(value)
        except ValueError:
            return value

    @staticmethod
    def _coerce_target(value: str, task_type: str) -> Any:
        """Coerce the target into the correct numeric or categorical type."""

        if task_type == "regression":
            return float(value)
        return value