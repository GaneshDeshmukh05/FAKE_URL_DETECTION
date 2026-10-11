"""Thread-safe loading and inference for the trained URL model bundle."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.config import EXPLAINER_PATH, MODEL_CONFIG_PATH, MODEL_PATH
from src.explainability import individual_contributions
from src.feature_engineering import FEATURE_NAMES, extract_features


class ModelUnavailableError(RuntimeError):
    """A trained compatible model bundle is not yet available to the API."""


class ModelService:
    """Load one matching model/explainer bundle and analyze validated URLs."""

    def __init__(self, model_path: Path = MODEL_PATH, explainer_path: Path = EXPLAINER_PATH, config_path: Path = MODEL_CONFIG_PATH):
        self.model_path = Path(model_path)
        self.explainer_path = Path(explainer_path)
        self.config_path = Path(config_path)
        self.model: Any | None = None
        self.explainer: Any | None = None
        self.feature_columns: list[str] = list(FEATURE_NAMES)
        self.threshold = 0.5

    def load(self) -> None:
        """Load artifacts and enforce their documented feature schema."""
        if self.model is not None and self.explainer is not None:
            return
        missing = [str(path.name) for path in (self.model_path, self.explainer_path, self.config_path) if not path.exists()]
        if missing:
            raise ModelUnavailableError(f"Trained model bundle is unavailable ({', '.join(missing)}). Run `python -m experiments.run_all` first.")
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
            feature_columns = list(config["feature_columns"])
            if feature_columns != list(FEATURE_NAMES):
                raise ModelUnavailableError("Model feature schema does not match this API version")
            self.model = joblib.load(self.model_path)
            self.explainer = joblib.load(self.explainer_path)
            self.feature_columns = feature_columns
            self.threshold = float(config["selected_threshold"])
        except ModelUnavailableError:
            raise
        except Exception as error:  # Serialized artifacts can be package-version sensitive.
            raise ModelUnavailableError(f"Could not load the trained model bundle: {error}") from error

    @staticmethod
    def _risk_level(probability: float) -> str:
        if probability >= 0.80:
            return "critical"
        if probability >= 0.60:
            return "high"
        if probability >= 0.40:
            return "medium"
        return "low"

    def analyze(self, url: str) -> dict[str, object]:
        """Return a model prediction and signed SHAP explanation for one URL."""
        self.load()
        assert self.model is not None and self.explainer is not None
        feature_values = extract_features(url)
        features = pd.DataFrame([[feature_values[name] for name in self.feature_columns]], columns=self.feature_columns)
        probability = float(self.model.predict_proba(features)[0, 1])
        contributions = individual_contributions(self.explainer, features)
        positive = sorted(((name, value) for name, value in contributions.items() if value > 0), key=lambda item: item[1], reverse=True)[:3]
        negative = sorted(((name, value) for name, value in contributions.items() if value < 0), key=lambda item: item[1])[:3]
        if not positive:
            positive = sorted(contributions.items(), key=lambda item: item[1], reverse=True)[:3]
        if not negative:
            negative = sorted(contributions.items(), key=lambda item: item[1])[:3]
        is_phishing = probability >= self.threshold
        rounded_contributions = {name: round(value, 6) for name, value in contributions.items()}
        return {
            "url": url,
            "prediction": "phishing" if is_phishing else "legitimate",
            "phishing_probability": round(probability, 6),
            "risk_score": int(round(probability * 100)),
            "confidence": round(max(probability, 1 - probability), 6),
            "risk_level": self._risk_level(probability),
            "operating_threshold": self.threshold,
            "extracted_features": {name: float(value) for name, value in feature_values.items()},
            "top_risk_factors": [{"feature": name, "shap_value": round(value, 6), "direction": "phishing"} for name, value in positive],
            "top_legitimate_factors": [{"feature": name, "shap_value": round(value, 6), "direction": "legitimate"} for name, value in negative],
            "top_features": [name for name, _ in positive],
            "shap_contributions": rounded_contributions,
            "shap_explanation": rounded_contributions,
        }


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Provide a process-wide lazily loaded service for FastAPI handlers."""
    return ModelService()
