"""Carga datos DEMO claramente identificables para probar Flask y Power BI sin APIs externas."""
from datetime import date, timedelta
from app.db import init_db
from app.repository import upsert_market_rows, upsert_prediction

TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY", "QQQ"]


def main():
    init_db()
    today = date.today()
    # Valores sinteticos: NO representan cotizaciones reales.
    for i, ticker in enumerate(TICKERS):
        upsert_market_rows([{
            "ticker": ticker,
            "date": today,
            "open": 100.0 + i * 5,
            "high": 103.0 + i * 5,
            "low": 98.0 + i * 5,
            "close": 101.5 + i * 5,
            "volume": 1_000_000 + i * 100_000,
            "source": "demo_synthetic",
        }])

    probs = [0.82, 0.78, 0.73, 0.68, 0.64, 0.60, 0.57]
    sentiments = [0.31, 0.21, 0.18, 0.08, 0.12, 0.02, 0.05]
    for rank, (ticker, prob, sent) in enumerate(zip(TICKERS, probs, sentiments), start=1):
        upsert_prediction({
            "ticker": ticker,
            "as_of_date": today,
            "probability_favorable": prob,
            "sentiment_score": sent,
            "model_version": "DEMO-SYNTHETIC",
            "horizon_days": 126,
            "rank_position": rank,
        })
    print("Datos DEMO sinteticos cargados. No usar como datos financieros reales.")


if __name__ == "__main__":
    main()
