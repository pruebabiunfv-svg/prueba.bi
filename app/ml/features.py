import pandas as pd
import numpy as np
from sqlalchemy import text
from app.db import engine

MARKET_FEATURES = [
    "ret_5",
    "ret_20",
    "ma_ratio_20",
    "ma_ratio_50",
    "volatility_20",
    "volume_ratio_20",
]
OPTIONAL_FEATURES = [
    "sentiment_score",
    "fred_CPIAUCSL",
    "fred_FEDFUNDS",
    "fred_UNRATE",
    "fund_revenue",
    "fund_net_income",
    "fund_assets",
]
ALL_FEATURES = MARKET_FEATURES + OPTIONAL_FEATURES


def load_feature_frame(horizon_days: int = 126) -> pd.DataFrame:
    market = pd.read_sql(text("SELECT ticker, date, close, volume FROM market_prices ORDER BY ticker, date"), engine)
    if market.empty:
        return pd.DataFrame()
    market["date"] = pd.to_datetime(market["date"])
    market = market.sort_values(["ticker", "date"]).reset_index(drop=True)

    g = market.groupby("ticker", group_keys=False)
    market["ret_5"] = g["close"].pct_change(5)
    market["ret_20"] = g["close"].pct_change(20)
    market["ma20"] = g["close"].transform(lambda s: s.rolling(20).mean())
    market["ma50"] = g["close"].transform(lambda s: s.rolling(50).mean())
    market["ma_ratio_20"] = market["close"] / market["ma20"] - 1
    market["ma_ratio_50"] = market["close"] / market["ma50"] - 1
    market["daily_ret"] = g["close"].pct_change()
    market["volatility_20"] = g["daily_ret"].transform(lambda s: s.rolling(20).std())
    market["volume_ma20"] = g["volume"].transform(lambda s: s.rolling(20).mean())
    market["volume_ratio_20"] = market["volume"] / market["volume_ma20"].replace(0, np.nan)
    market["future_close"] = g["close"].shift(-horizon_days)
    market["future_return"] = market["future_close"] / market["close"] - 1
    market["target"] = np.where(market["future_return"].notna(), (market["future_return"] > 0).astype(int), np.nan)

    market = _merge_sentiment(market)
    market = _merge_macro(market)
    market = _merge_fundamentals(market)

    for col in OPTIONAL_FEATURES:
        if col not in market.columns:
            market[col] = np.nan

    return market


def latest_feature_rows(horizon_days: int = 126) -> pd.DataFrame:
    frame = load_feature_frame(horizon_days=horizon_days)
    if frame.empty:
        return frame
    # Para prediccion actual no se requiere target/future_close.
    latest = frame.sort_values(["ticker", "date"]).groupby("ticker", as_index=False).tail(1)
    return latest.reset_index(drop=True)


def _merge_sentiment(market: pd.DataFrame) -> pd.DataFrame:
    try:
        news = pd.read_sql(text("SELECT ticker, published_at, sentiment_score FROM news_sentiment"), engine)
    except Exception:
        return market
    if news.empty:
        market["sentiment_score"] = 0.0
        return market
    news["date"] = pd.to_datetime(news["published_at"]).dt.normalize()
    daily = news.groupby(["ticker", "date"], as_index=False)["sentiment_score"].mean()
    out = market.merge(daily, on=["ticker", "date"], how="left")
    # Sentimiento reciente: arrastre corto; no se rellena todo el historico con una sola noticia.
    out["sentiment_score"] = out.groupby("ticker")["sentiment_score"].transform(lambda s: s.ffill(limit=5)).fillna(0.0)
    return out


def _merge_macro(market: pd.DataFrame) -> pd.DataFrame:
    try:
        macro = pd.read_sql(text("SELECT series_id, date, value FROM macro_indicators"), engine)
    except Exception:
        return market
    if macro.empty:
        return market
    macro["date"] = pd.to_datetime(macro["date"])
    pivot = macro.pivot_table(index="date", columns="series_id", values="value", aggfunc="last").reset_index()
    rename = {c: f"fred_{c}" for c in pivot.columns if c != "date"}
    pivot = pivot.rename(columns=rename).sort_values("date")

    parts = []
    for ticker, group in market.groupby("ticker", sort=False):
        merged = pd.merge_asof(group.sort_values("date"), pivot, on="date", direction="backward")
        parts.append(merged)
    return pd.concat(parts, ignore_index=True) if parts else market


def _merge_fundamentals(market: pd.DataFrame) -> pd.DataFrame:
    try:
        fund = pd.read_sql(text("SELECT ticker, as_of_date, metric, value FROM fundamentals"), engine)
    except Exception:
        return market
    if fund.empty:
        return market
    fund["as_of_date"] = pd.to_datetime(fund["as_of_date"])
    pivot = fund.pivot_table(index=["ticker", "as_of_date"], columns="metric", values="value", aggfunc="last").reset_index()
    pivot = pivot.rename(columns={
        "revenue": "fund_revenue",
        "net_income": "fund_net_income",
        "assets": "fund_assets",
    })

    parts = []
    for ticker, group in market.groupby("ticker", sort=False):
        f = pivot[pivot["ticker"] == ticker].sort_values("as_of_date").drop(columns=["ticker"], errors="ignore")
        if f.empty:
            parts.append(group)
            continue
        merged = pd.merge_asof(
            group.sort_values("date"),
            f,
            left_on="date",
            right_on="as_of_date",
            direction="backward",
        ).drop(columns=["as_of_date"], errors="ignore")
        parts.append(merged)
    return pd.concat(parts, ignore_index=True) if parts else market
