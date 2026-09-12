from datetime import datetime
import requests
import yfinance as yf
from app.config import Config


def fetch_yahoo_history(ticker: str, period: str | None = None) -> list[dict]:
    period = period or Config.MARKET_PERIOD
    frame = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    if frame.empty:
        return []

    # yfinance puede retornar MultiIndex incluso para un solo ticker.
    if hasattr(frame.columns, "levels"):
        frame.columns = [c[0] if isinstance(c, tuple) else c for c in frame.columns]

    records = []
    for idx, row in frame.iterrows():
        records.append({
            "ticker": ticker.upper(),
            "date": idx.date(),
            "open": _float_or_none(row.get("Open")),
            "high": _float_or_none(row.get("High")),
            "low": _float_or_none(row.get("Low")),
            "close": _float_or_none(row.get("Close")),
            "volume": _float_or_none(row.get("Volume")),
            "source": "yahoo",
        })
    return [r for r in records if r["close"] is not None]


def fetch_alpha_vantage_daily(ticker: str) -> list[dict]:
    """Fuente alternativa. Requiere ALPHA_VANTAGE_API_KEY."""
    if not Config.ALPHA_VANTAGE_API_KEY:
        raise RuntimeError("ALPHA_VANTAGE_API_KEY no esta configurado")

    response = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "full",
            "apikey": Config.ALPHA_VANTAGE_API_KEY,
        },
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    series = payload.get("Time Series (Daily)", {})
    records = []
    for date_text, values in series.items():
        records.append({
            "ticker": ticker.upper(),
            "date": datetime.strptime(date_text, "%Y-%m-%d").date(),
            "open": _float_or_none(values.get("1. open")),
            "high": _float_or_none(values.get("2. high")),
            "low": _float_or_none(values.get("3. low")),
            "close": _float_or_none(values.get("4. close")),
            "volume": _float_or_none(values.get("5. volume")),
            "source": "alpha_vantage",
        })
    return records


def _float_or_none(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
