"""Validated public API request and response contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.feature_engineering import InvalidURLException, normalise_url


class URLRequest(BaseModel):
    """One URL to classify. URL analysis is entirely offline."""

    url: str = Field(..., min_length=1, max_length=4096, description="HTTP(S) URL or schemeless hostname/path")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        try:
            normalise_url(value)
        except InvalidURLException as error:
            raise ValueError(str(error)) from error
        return value.strip()


class RiskFactor(BaseModel):
    feature: str
    shap_value: float
    direction: Literal["phishing", "legitimate"]


class URLAnalysisResponse(BaseModel):
    url: str
    prediction: Literal["phishing", "legitimate"]
    phishing_probability: float = Field(..., ge=0, le=1)
    risk_score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    risk_level: Literal["low", "medium", "high", "critical"]
    operating_threshold: float = Field(..., ge=0, le=1)
    extracted_features: dict[str, float]
    top_risk_factors: list[RiskFactor]
    top_legitimate_factors: list[RiskFactor]
    # Legacy aliases retained for clients of the original API.
    top_features: list[str]
    shap_contributions: dict[str, float]
    shap_explanation: dict[str, float]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    feature_count: int
    operating_threshold: float
