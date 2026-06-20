from __future__ import annotations

import hashlib
import json
import os
import time
from collections import OrderedDict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"


def load_env_file(path: Path = BASE_DIR / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def env_path(name: str, default: Path) -> Path:
    configured = os.getenv(name, "").strip()
    if not configured:
        return default

    path = Path(configured)
    return path if path.is_absolute() else BASE_DIR / path


load_env_file()

DATASET_PATH = env_path("DATASET_PATH", BASE_DIR / "loan_approval_dataset.csv")
MODEL_PATHS = [
    env_path("MODEL_PATH", BASE_DIR / "backend" / "model.pkl"),
    BASE_DIR / "loan_approval_model.pkl",
]
SCALER_PATHS = [
    env_path("PREPROCESSOR_PATH", BASE_DIR / "backend" / "preprocessor.pkl"),
    env_path("SCALER_PATH", BASE_DIR / "scaler.pkl"),
]

FEATURES = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

NUMERIC_FEATURES = [
    "no_of_dependents",
    "income_annum",
    "loan_amount",
    "loan_term",
    "cibil_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

DEFAULT_DEPENDENTS = 0
LABELS = {0: "Approved", 1: "Rejected"}

# ---------------------------------------------------------------------------
# Response cache for Mistral API calls
# ---------------------------------------------------------------------------
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "128"))

_mistral_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()


def _cache_key(messages: list[dict[str, str]], max_tokens: int) -> str:
    """Deterministic hash of the request so identical prompts hit the cache."""
    raw = json.dumps({"m": messages, "t": max_tokens}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> str | None:
    entry = _mistral_cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > CACHE_TTL:
        _mistral_cache.pop(key, None)
        return None
    # Move to end so LRU eviction stays correct
    _mistral_cache.move_to_end(key)
    return value


def _cache_put(key: str, value: str) -> None:
    _mistral_cache[key] = (time.monotonic(), value)
    _mistral_cache.move_to_end(key)
    while len(_mistral_cache) > CACHE_MAX_SIZE:
        _mistral_cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Cached dataset stats
# ---------------------------------------------------------------------------
_stats_cache: dict | None = None


def _compute_stats(df: pd.DataFrame) -> dict:
    status = df["loan_status"].str.strip()
    return {
        "rows": int(len(df)),
        "null_values": int(df.isnull().sum().sum()),
        "approved": int((status == "Approved").sum()),
        "rejected": int((status == "Rejected").sum()),
    }


def _get_dataset_summary(df: pd.DataFrame) -> str:
    """Build a compact text summary of the dataset for Mistral context."""
    status = df["loan_status"].str.strip()
    numeric_cols = df.select_dtypes(include="number")
    summary_lines = [
        f"Dataset: {len(df)} rows, {len(df.columns)} columns.",
        f"Approved: {int((status == 'Approved').sum())}, Rejected: {int((status == 'Rejected').sum())}.",
        f"Columns: {', '.join(df.columns.tolist())}.",
        "Key numeric stats:",
    ]
    for col in numeric_cols.columns:
        summary_lines.append(
            f"  {col}: mean={numeric_cols[col].mean():.0f}, "
            f"min={numeric_cols[col].min():.0f}, "
            f"max={numeric_cols[col].max():.0f}"
        )
    return "\n".join(summary_lines)


# ---------------------------------------------------------------------------


def first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    CORS(app)

    model_path = first_existing(MODEL_PATHS)
    scaler_path = first_existing(SCALER_PATHS)
    model = joblib.load(model_path) if model_path else None
    scaler = joblib.load(scaler_path) if scaler_path else None

    # Pre-compute dataset summary once at startup for /query context
    _dataset_summary: str | None = None
    try:
        _startup_df = load_dataset()
        _dataset_summary = _get_dataset_summary(_startup_df)
    except Exception:
        _dataset_summary = None

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "running"})

    @app.get("/stats")
    def stats():
        global _stats_cache
        if _stats_cache is not None:
            return jsonify(_stats_cache)
        df = load_dataset()
        _stats_cache = _compute_stats(df)
        return jsonify(_stats_cache)

    @app.post("/predict")
    def predict():
        payload = request.get_json(silent=True) or {}

        try:
            features = normalize_payload(payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        prediction_id, probabilities = predict_with_artifacts(features, model, scaler)
        prediction = LABELS.get(prediction_id, "Approved")
        probability = probabilities[prediction]

        explanation = build_local_explanation(features, prediction, probability)
        if payload.get("include_explanation", True):
            explanation = build_mistral_explanation(features, prediction, probability, explanation)

        return jsonify(
            {
                "prediction": prediction,
                "probability": round(probability, 4),
                "approved_probability": round(probabilities["Approved"], 4),
                "rejected_probability": round(probabilities["Rejected"], 4),
                "confidence": round(probability * 100),
                "explanation": explanation,
            }
        )

    @app.post("/assistant")
    def assistant():
        payload = request.get_json(silent=True) or {}
        question = str(payload.get("question", "")).strip()
        context = payload.get("context") or {}
        if not question:
            return jsonify({"error": "question is required"}), 400

        fallback = build_assistant_fallback(question, context)
        user_payload = {
            "question": question,
            "bankpulse_context": compact_assistant_context(context),
        }
        answer = call_mistral(
            [
                {
                    "role": "system",
                    "content": (
                        "You are BankPulse Assist in a beginner ML loan-approval app. "
                        "Answer only about this app, its prediction, and these features: "
                        "education, self-employment, income, loan amount, loan term, "
                        "CIBIL score, and assets. Use prediction context when present. "
                        "Plain text only, no markdown. Under 50 words."
                    ),
                },
                {"role": "user", "content": json.dumps(user_payload, separators=(",", ":"))},
            ],
            fallback,
            max_tokens=65,
        )
        return jsonify({"answer": answer})

    @app.post("/query")
    def query():
        payload = request.get_json(silent=True) or {}
        user_query = str(payload.get("query", "")).strip()
        if not user_query:
            return jsonify({"error": "query is required"}), 400

        context_text = _dataset_summary or "Dataset context unavailable."
        fallback = (
            "I can answer questions about the BankPulse loan dataset — "
            "try asking about averages, counts, or ranges for columns like "
            "cibil_score, income_annum, or loan_amount."
        )

        answer = call_mistral(
            [
                {
                    "role": "system",
                    "content": (
                        "You are BankPulse Query, a data assistant for a loan-approval dataset. "
                        "Use the dataset summary below to answer the user's question accurately. "
                        "Give a direct, concise answer with numbers when possible. "
                        "Plain text only, no markdown. Under 60 words.\n\n"
                        f"{context_text}"
                    ),
                },
                {"role": "user", "content": user_query},
            ],
            fallback,
            max_tokens=70,
        )
        return jsonify({"answer": answer, "query": user_query})

    return app


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip()
    return df


def normalize_payload(payload: dict) -> dict:
    values = {"no_of_dependents": payload.get("no_of_dependents", DEFAULT_DEPENDENTS)}

    for key in FEATURES:
        if key in values:
            continue
        if key not in payload or payload[key] in ("", None):
            raise ValueError(f"{key} is required")
        values[key] = payload[key]

    for key in NUMERIC_FEATURES:
        try:
            values[key] = float(values[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a number") from exc

    values["education"] = encode_choice(values["education"], {"graduate": 0, "not graduate": 1}, "education")
    values["self_employed"] = encode_choice(values["self_employed"], {"no": 0, "yes": 1}, "self_employed")
    return values


def encode_choice(value: object, mapping: dict[str, int], field_name: str) -> int:
    normalized = str(value).strip().lower()
    if normalized not in mapping:
        valid = ", ".join(mapping)
        raise ValueError(f"{field_name} must be one of: {valid}")
    return mapping[normalized]


def predict_with_artifacts(features: dict, model, scaler) -> tuple[int, dict[str, float]]:
    frame = pd.DataFrame([[features[name] for name in FEATURES]], columns=FEATURES)

    if model is not None and scaler is not None:
        scaled = scaler.transform(frame)
        prediction_id = int(model.predict(scaled)[0])

        if hasattr(model, "predict_proba"):
            raw_probabilities = model.predict_proba(scaled)[0]
            class_probabilities = {
                LABELS.get(int(class_id), str(class_id)): float(raw_probabilities[index])
                for index, class_id in enumerate(model.classes_)
            }
            return prediction_id, {
                "Approved": class_probabilities.get("Approved", 0.0),
                "Rejected": class_probabilities.get("Rejected", 0.0),
            }

        return prediction_id, {LABELS[prediction_id]: 1.0, LABELS[1 - prediction_id]: 0.0}

    approved_probability = fallback_approved_probability(features)
    prediction_id = 0 if approved_probability >= 0.5 else 1
    return prediction_id, {"Approved": approved_probability, "Rejected": 1 - approved_probability}


def fallback_approved_probability(features: dict) -> float:
    cibil_score = features["cibil_score"]
    income = max(features["income_annum"], 1)
    loan_ratio = features["loan_amount"] / income
    asset_total = (
        features["residential_assets_value"]
        + features["commercial_assets_value"]
        + features["luxury_assets_value"]
        + features["bank_asset_value"]
    )
    asset_ratio = asset_total / max(features["loan_amount"], 1)

    score = 0.25
    score += min(max((cibil_score - 450) / 400, 0), 1) * 0.45
    score += min(max((5 - loan_ratio) / 5, 0), 1) * 0.2
    score += min(asset_ratio / 3, 1) * 0.1
    return max(0.05, min(0.95, score))


def build_local_explanation(features: dict, prediction: str, probability: float) -> str:
    cibil_score = features["cibil_score"]
    loan_ratio = features["loan_amount"] / max(features["income_annum"], 1)
    asset_total = (
        features["residential_assets_value"]
        + features["commercial_assets_value"]
        + features["luxury_assets_value"]
        + features["bank_asset_value"]
    )

    reasons = []
    reasons.append(f"CIBIL score is {int(cibil_score)}, which is {'strong' if cibil_score >= 700 else 'moderate' if cibil_score >= 550 else 'low'}.")
    reasons.append(f"The loan is about {loan_ratio:.1f} times the annual income.")
    reasons.append(f"Declared assets total around {format_currency(asset_total)}.")
    return f"{prediction} with {round(probability * 100)}% confidence. " + " ".join(reasons)


def compact_assistant_context(context: dict) -> dict:
    if not isinstance(context, dict):
        return {}

    allowed_inputs = {
        key: context.get("inputs", {}).get(key)
        for key in [
            "education",
            "self_employed",
            "income_annum",
            "loan_amount",
            "loan_term",
            "cibil_score",
            "residential_assets_value",
            "commercial_assets_value",
            "luxury_assets_value",
            "bank_asset_value",
        ]
        if isinstance(context.get("inputs"), dict) and key in context.get("inputs", {})
    }

    return {
        "prediction": context.get("prediction"),
        "confidence": context.get("confidence"),
        "approved_probability": context.get("approved_probability"),
        "rejected_probability": context.get("rejected_probability"),
        "inputs": allowed_inputs,
    }


def build_assistant_fallback(question: str, context: dict) -> str:
    compact_context = compact_assistant_context(context)
    prediction = compact_context.get("prediction")
    inputs = compact_context.get("inputs", {})

    if not prediction or not inputs:
        return "Submit a loan application first, then I can explain the model result using CIBIL score, income, loan amount, term, and assets."

    cibil_score = float(inputs.get("cibil_score") or 0)
    income = max(float(inputs.get("income_annum") or 1), 1)
    loan_amount = float(inputs.get("loan_amount") or 0)
    loan_ratio = loan_amount / income

    if "improve" in question.lower() or "increase" in question.lower():
        return f"To improve this {prediction} result, focus on a stronger CIBIL score, a lower loan-to-income ratio, or higher bank/assets support."

    if "why" in question.lower() or "reason" in question.lower():
        return f"The model likely focused on CIBIL {int(cibil_score)}, a loan-to-income ratio near {loan_ratio:.1f}, loan term, and asset values."

    return f"This BankPulse result is {prediction}. CIBIL score, loan amount versus income, term, and declared assets are the main project features to inspect."


def build_mistral_explanation(features: dict, prediction: str, probability: float, fallback: str) -> str:
    prompt = {
        "result": prediction,
        "confidence": round(probability * 100),
        "edu": "Graduate" if features["education"] == 0 else "Not Graduate",
        "self_emp": "No" if features["self_employed"] == 0 else "Yes",
        "income": int(features["income_annum"]),
        "loan": int(features["loan_amount"]),
        "term": int(features["loan_term"]),
        "cibil": int(features["cibil_score"]),
        "assets": int(
            features["residential_assets_value"]
            + features["commercial_assets_value"]
            + features["luxury_assets_value"]
            + features["bank_asset_value"]
        ),
    }

    return call_mistral(
        [
            {
                "role": "system",
                "content": (
                    "Explain this BankPulse loan ML result in 2 short plain-text sentences. "
                    "Mention likely factors only. No markdown, no disclaimers."
                ),
            },
            {"role": "user", "content": json.dumps(prompt, separators=(",", ":"))},
        ],
        fallback,
        max_tokens=50,
    )


def call_mistral(messages: list[dict[str, str]], fallback: str, max_tokens: int | None = None) -> str:
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return fallback

    endpoint = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
    model_name = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    token_limit = max_tokens or int(os.getenv("MISTRAL_MAX_TOKENS", "70"))
    temperature = float(os.getenv("MISTRAL_TEMPERATURE", "0.15"))
    timeout = int(os.getenv("MISTRAL_TIMEOUT_SECONDS", "10"))

    # --- Check cache ---
    key = _cache_key(messages, token_limit)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    body = json.dumps(
        {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": token_limit,
        },
        separators=(",", ":"),
    ).encode()

    req = Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        result = data["choices"][0]["message"]["content"].strip()
        _cache_put(key, result)
        return result
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
        return fallback


def format_currency(value: float) -> str:
    return "₹{:,.0f}".format(value)


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
