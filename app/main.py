"""Production-facing FastAPI endpoints for URL-only phishing analysis."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, status

from .schemas import HealthResponse, URLAnalysisResponse, URLRequest
from .services.model_service import ModelUnavailableError, get_model_service


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("phishing_url_detector")

app = FastAPI(
    title="Explainable Phishing URL Detector",
    version="2.0.0",
    description="Offline URL-feature analysis with XGBoost and SHAP model explanations. SHAP explains model behavior; it is not causal evidence.",
)


@app.get("/health", response_model=HealthResponse, tags=["operational"])
def health() -> HealthResponse:
    """Verify that a compatible trained model bundle can be loaded."""
    try:
        service = get_model_service()
        service.load()
        return HealthResponse(status="ok", model_loaded=True, feature_count=len(service.feature_columns), operating_threshold=service.threshold)
    except ModelUnavailableError as error:
        logger.error("Health check failed: %s", error)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@app.post("/analyze-url", response_model=URLAnalysisResponse, tags=["analysis"])
def analyze_url(payload: URLRequest) -> URLAnalysisResponse:
    """Classify one validated URL and return model-interpretation information."""
    try:
        result = get_model_service().analyze(payload.url)
        logger.info("URL analyzed: prediction=%s probability=%.4f", result["prediction"], result["phishing_probability"])
        return URLAnalysisResponse(**result)
    except ModelUnavailableError as error:
        logger.error("Analysis unavailable: %s", error)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except Exception as error:
        logger.exception("Unexpected URL analysis error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="URL analysis failed") from error
