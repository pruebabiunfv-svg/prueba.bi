import hmac
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from app.config import Config
from app.db import engine
from app.repository import (
    get_assets,
    get_latest_market_snapshot,
    get_latest_prediction_for_ticker,
    get_latest_predictions,
    get_latest_sentiment_for_ticker,
    get_prediction_history,
)
from app.services.huggingface_finbert import classify_financial_text

api = Blueprint("api", __name__, url_prefix="/api")


def _pbi_authorized() -> bool:
    expected = Config.PBI_API_KEY
    if not expected:
        return True
    supplied = request.args.get("api_key", "")
    return bool(supplied) and hmac.compare_digest(supplied, expected)


@api.get("/health")
def health():
    db_ok = False
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # health endpoint should expose only a concise error
        db_error = exc.__class__.__name__

    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "app": Config.APP_NAME,
        "database": "ok" if db_ok else db_error,
        "huggingface_configured": bool(Config.HF_TOKEN),
        "demo_mode": Config.DEMO_MODE,
    }), 200 if db_ok else 503


@api.get("/assets")
def assets():
    values = get_assets() or Config.TICKERS
    return jsonify({"assets": values})


@api.get("/dashboard")
def dashboard():
    predictions = get_latest_predictions()
    rows = []
    for pred in predictions:
        market = get_latest_market_snapshot(pred["ticker"]) or {}
        rows.append({**pred, "latest_close": market.get("close"), "market_date": market.get("date")})
    return jsonify({
        "project": Config.APP_NAME,
        "horizon_days": Config.PREDICTION_HORIZON_DAYS,
        "count": len(rows),
        "ranking": rows,
    })


@api.get("/predict/<ticker>")
def predict(ticker: str):
    item = get_latest_prediction_for_ticker(ticker)
    if not item:
        return jsonify({
            "error": "prediction_not_found",
            "detail": "Ejecute el pipeline y entrene XGBoost antes de consultar la prediccion.",
        }), 404
    return jsonify(item)


@api.get("/sentiment/<ticker>")
def sentiment(ticker: str):
    days = request.args.get("days", default=7, type=int)
    return jsonify(get_latest_sentiment_for_ticker(ticker, days=max(1, min(days, 90))))


@api.post("/sentiment/analyze")
def sentiment_analyze():
    payload = request.get_json(silent=True) or {}
    value = (payload.get("text") or "").strip()
    if not value:
        return jsonify({"error": "text_required"}), 400
    try:
        result = classify_financial_text(value)
        return jsonify({
            "label": result.label,
            "sentiment_score": result.score,
            "probabilities": result.probabilities,
            "model": Config.HF_MODEL,
            "source": result.inference_source,
        })
    except Exception as exc:
        return jsonify({"error": "huggingface_error", "detail": str(exc)}), 502


@api.get("/pbi/dashboard")
def pbi_dashboard():
    if not _pbi_authorized():
        return jsonify({"error": "unauthorized"}), 401

    predictions = get_latest_predictions()
    output = []
    for pred in predictions:
        market = get_latest_market_snapshot(pred["ticker"]) or {}
        output.append({
            "Ticker": pred["ticker"],
            "Fecha": pred["as_of_date"],
            "Ranking": pred["rank_position"],
            "ProbabilidadFavorable": pred["probability_favorable"],
            "ProbabilidadPct": pred["probability_pct"],
            "SentimientoScore": pred["sentiment_score"],
            "HorizonteDias": pred["horizon_days"],
            "Modelo": pred["model_version"],
            "UltimoPrecio": market.get("close"),
            "FechaMercado": market.get("date"),
        })
    return jsonify(output)


@api.get("/pbi/history")
def pbi_history():
    if not _pbi_authorized():
        return jsonify({"error": "unauthorized"}), 401
    days = request.args.get("days", default=365, type=int)
    return jsonify(get_prediction_history(days=days))
