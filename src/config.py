"""Central paths and deterministic experiment settings."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
SHAP_RESULTS_DIR = RESULTS_DIR / "shap"

RANDOM_SEED = 42
TEST_SIZE = 0.20
CV_FOLDS = 3
DEFAULT_THRESHOLD = 0.50

PRIMARY_DATASET = Path(os.getenv("PHISHING_PRIMARY_DATASET", DATA_DIR / "phishing.csv"))
CROSS_DATASET = Path(os.getenv("PHISHING_CROSS_DATASET", DATA_DIR / "raw_data.csv"))
MODEL_PATH = Path(os.getenv("PHISHING_MODEL_PATH", MODELS_DIR / "xgboost_url_model.joblib"))
EXPLAINER_PATH = Path(os.getenv("PHISHING_EXPLAINER_PATH", MODELS_DIR / "shap_url_explainer.joblib"))
MODEL_CONFIG_PATH = MODELS_DIR / "best_xgboost_config.json"
FEATURE_MANIFEST_PATH = MODELS_DIR / "feature_manifest.json"


def ensure_output_directories() -> None:
    """Create the non-source directories used by reproducible experiments."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SHAP_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
