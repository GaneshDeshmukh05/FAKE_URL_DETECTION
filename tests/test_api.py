import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.model_service import ModelService
from src.feature_engineering import FEATURE_NAMES


class FakeModel:
    def predict_proba(self, features):
        return np.array([[0.2, 0.8] for _ in range(len(features))])


class FakeExplanation:
    def __init__(self, width):
        self.values = np.array([[0.1] * width])


class FakeExplainer:
    def __call__(self, features):
        return FakeExplanation(features.shape[1])


def fake_service() -> ModelService:
    service = ModelService()
    service.model = FakeModel()
    service.explainer = FakeExplainer()
    service.feature_columns = list(FEATURE_NAMES)
    service.threshold = 0.5
    return service


def test_model_service_prediction_with_shap_explanation():
    result = fake_service().analyze("https://example.com/login")
    assert result["prediction"] == "phishing"
    assert result["phishing_probability"] == 0.8
    assert len(result["shap_contributions"]) == len(FEATURE_NAMES)


def test_api_rejects_invalid_url():
    client = TestClient(app)
    response = client.post("/analyze-url", json={"url": "ftp://example.com"})
    assert response.status_code == 422


def test_api_returns_validated_analysis(monkeypatch):
    monkeypatch.setattr("app.main.get_model_service", fake_service)
    client = TestClient(app)
    response = client.post("/analyze-url", json={"url": "https://example.com/login"})
    assert response.status_code == 200
    body = response.json()
    assert body["prediction"] == "phishing"
    assert body["top_risk_factors"]
