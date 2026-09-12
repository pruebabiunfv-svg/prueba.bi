"""ETL + NLP + ML. Diseñado para ejecutarse y terminar como Railway Cron Job."""
import json
import traceback

from app.config import Config
from app.db import init_db
from app.repository import (
    add_news_row,
    upsert_fundamental_rows,
    upsert_macro_rows,
    upsert_market_rows,
)
from app.services.market import fetch_yahoo_history, fetch_alpha_vantage_daily
from app.services.fred import fetch_fred_series, DEFAULT_SERIES
from app.services.sec_edgar import fetch_company_fundamentals
from app.services.gdelt import fetch_gdelt_news
from app.services.huggingface_finbert import classify_financial_text
from app.ml.train_xgboost import train_model, walk_forward_validate


def run_step(name, fn):
    try:
        result = fn()
        print(json.dumps({"step": name, "status": "ok", "result": result}, default=str))
        return result
    except Exception as exc:
        print(json.dumps({"step": name, "status": "error", "error": str(exc)}))
        traceback.print_exc()
        return None


def load_market():
    total = 0
    for ticker in Config.TICKERS:
        rows = fetch_yahoo_history(ticker)
        if not rows and Config.ALPHA_VANTAGE_API_KEY:
            print(f"Yahoo sin datos para {ticker}; usando Alpha Vantage como fallback")
            rows = fetch_alpha_vantage_daily(ticker)
        total += upsert_market_rows(rows)
        print(f"market {ticker}: {len(rows)}")
    return {"rows": total}


def load_macro():
    if not Config.FRED_API_KEY:
        return {"skipped": "FRED_API_KEY ausente"}
    total = 0
    for series_id in DEFAULT_SERIES:
        rows = fetch_fred_series(series_id)
        total += upsert_macro_rows(rows)
    return {"rows": total, "series": DEFAULT_SERIES}


def load_fundamentals():
    total = 0
    for ticker in Config.TICKERS:
        rows = fetch_company_fundamentals(ticker)
        total += upsert_fundamental_rows(rows)
    return {"rows": total}


def load_news_sentiment():
    if not Config.HF_TOKEN and not Config.HF_ALLOW_NEUTRAL_FALLBACK:
        return {"skipped": "HF_TOKEN ausente"}
    inserted = 0
    attempted = 0
    for ticker in Config.TICKERS:
        try:
            articles = fetch_gdelt_news(ticker)
        except Exception as exc:
            print(f"GDELT {ticker}: {exc}")
            continue
        for article in articles:
            attempted += 1
            try:
                sentiment = classify_financial_text(article["title"])
                article.update({
                    "sentiment_label": sentiment.label,
                    "sentiment_score": sentiment.score,
                    "model_name": Config.HF_MODEL,
                    "inference_source": sentiment.inference_source,
                })
                inserted += int(add_news_row(article))
            except Exception as exc:
                print(f"FinBERT {ticker}: {exc}")
    return {"attempted": attempted, "inserted": inserted}


def main():
    init_db()
    run_step("market", load_market)
    run_step("macro_fred", load_macro)
    run_step("fundamentals_sec", load_fundamentals)
    run_step("news_gdelt_finbert", load_news_sentiment)
    metrics = run_step("xgboost_train", train_model)
    if metrics:
        run_step("walk_forward", lambda: walk_forward_validate(n_splits=4))
    print(json.dumps({"pipeline": "finished"}))


if __name__ == "__main__":
    main()
