# Explainable and Robust Phishing URL Detection

This project is a URL-only phishing detector built around engineered lexical and
structural URL features, XGBoost, and SHAP explanations. It upgrades the
original FastAPI + XGBoost + SHAP implementation without visiting submitted URLs
or adding WHOIS, browser, CNN, or LLM dependencies.

## What is preserved and improved

`POST /analyze-url` remains the inference endpoint and `uvicorn main:app`
remains the server command. The former notebook training procedure and 12
useful lexical features are preserved conceptually, but training and serving
now share a single extractor and the trained research model has a documented
26-feature schema. The original `xgboost_model.pkl` and `shap_explainer.pkl`
are left untouched as legacy artifacts; the upgraded model is written under
`models/`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The checked-in data paths default to `phishing.csv` (primary PhiUSIIL-style
source) and `raw_data.csv` (external two-column source). Configure replacements
as described in [CONFIG.md](CONFIG.md).

## Reproduce the full experiment package

```powershell
python -m experiments.run_all --tuning-iterations 8
```

This command cleans data, creates both random and domain-disjoint splits,
tunes XGBoost only on training-domain folds, selects an operating threshold
from training OOF scores, trains the final model, and writes actual outputs to
`models/` and `results/`. It may take several minutes on the supplied datasets.
Use a smaller number such as `--tuning-iterations 2` only for a smoke test; it
is not the recommended research run.

Key outputs are:

* `models/best_xgboost_config.json` — selected parameters, CV score, threshold, and schema.
* `results/model_comparison.csv` / `.png` — baseline results from the same fixed unseen-domain test set.
* `results/ablation_results.csv` / `.png` — cumulative feature-group ablation.
* `results/zero_day_results.csv` — fixed unseen-domain holdout results.
* `results/cross_dataset_results.csv` — external dataset results after removing all primary-domain overlaps.
* `results/robustness_results.csv` — offline perturbation outcomes; no URLs are visited.
* `results/threshold_results.csv`, `latency_results.csv`, curves, confusion matrix, and `results/shap/` plots.

Do not treat a successful run as evidence of causal feature effects or of
superiority to other papers. See [EXPERIMENTS.md](EXPERIMENTS.md) for the
protocol and limitations.

## Run the API

Run the experiments once so that the compatible model bundle exists, then:

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/analyze-url -Method Post -ContentType 'application/json' -Body '{"url":"https://example.com/login"}'
```

The response contains the phishing probability, selected operating threshold,
risk level, extracted features, signed SHAP contributions, and top model risk
and legitimate factors. SHAP is an explanation of the model's score, not a
causal conclusion about the URL.

## Test

```powershell
pytest -q
```

The tests cover URL validation/parsing, feature extraction, cleaning/split
leakage protection, model-service prediction behavior, and API validation.
# FAKE_URL_DETECTION
