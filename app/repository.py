from datetime import date, datetime, timedelta
from sqlalchemy import select, func, desc
from app.db import session_scope
from app.models import MarketPrice, MacroIndicator, Fundamental, NewsSentiment, Prediction, BacktestResult


def upsert_market_rows(rows: list[dict]) -> int:
    count = 0
    with session_scope() as session:
        for row in rows:
            obj = session.execute(
                select(MarketPrice).where(
                    MarketPrice.ticker == row["ticker"],
                    MarketPrice.date == row["date"],
                )
            ).scalar_one_or_none()
            if obj is None:
                session.add(MarketPrice(**row))
            else:
                for key, value in row.items():
                    setattr(obj, key, value)
            count += 1
    return count


def upsert_macro_rows(rows: list[dict]) -> int:
    count = 0
    with session_scope() as session:
        for row in rows:
            obj = session.execute(
                select(MacroIndicator).where(
                    MacroIndicator.series_id == row["series_id"],
                    MacroIndicator.date == row["date"],
                )
            ).scalar_one_or_none()
            if obj is None:
                session.add(MacroIndicator(**row))
            else:
                obj.value = row.get("value")
                obj.source = row.get("source", obj.source)
            count += 1
    return count


def upsert_fundamental_rows(rows: list[dict]) -> int:
    count = 0
    with session_scope() as session:
        for row in rows:
            obj = session.execute(
                select(Fundamental).where(
                    Fundamental.ticker == row["ticker"],
                    Fundamental.as_of_date == row["as_of_date"],
                    Fundamental.metric == row["metric"],
                )
            ).scalar_one_or_none()
            if obj is None:
                session.add(Fundamental(**row))
            else:
                obj.value = row.get("value")
                obj.unit = row.get("unit", obj.unit)
                obj.source = row.get("source", obj.source)
            count += 1
    return count


def add_news_row(row: dict) -> bool:
    with session_scope() as session:
        existing = session.execute(
            select(NewsSentiment).where(
                NewsSentiment.ticker == row["ticker"],
                NewsSentiment.title == row["title"],
                NewsSentiment.published_at == row["published_at"],
            )
        ).scalar_one_or_none()
        if existing:
            return False
        session.add(NewsSentiment(**row))
        return True


def upsert_prediction(row: dict) -> None:
    with session_scope() as session:
        obj = session.execute(
            select(Prediction).where(
                Prediction.ticker == row["ticker"],
                Prediction.as_of_date == row["as_of_date"],
            )
        ).scalar_one_or_none()
        if obj is None:
            session.add(Prediction(**row))
        else:
            for key, value in row.items():
                setattr(obj, key, value)


def add_backtest_result(row: dict) -> None:
    with session_scope() as session:
        session.add(BacktestResult(**row))


def get_latest_predictions() -> list[dict]:
    with session_scope() as session:
        latest_date = session.execute(select(func.max(Prediction.as_of_date))).scalar_one_or_none()
        if not latest_date:
            return []
        items = session.execute(
            select(Prediction).where(Prediction.as_of_date == latest_date).order_by(
                Prediction.rank_position.asc().nullslast(), Prediction.probability_favorable.desc()
            )
        ).scalars().all()
        return [_prediction_to_dict(x) for x in items]


def get_prediction_history(days: int = 365) -> list[dict]:
    since = date.today() - timedelta(days=max(1, min(days, 3650)))
    with session_scope() as session:
        items = session.execute(
            select(Prediction).where(Prediction.as_of_date >= since).order_by(
                Prediction.as_of_date.asc(), Prediction.ticker.asc()
            )
        ).scalars().all()
        return [_prediction_to_dict(x) for x in items]


def get_latest_prediction_for_ticker(ticker: str):
    with session_scope() as session:
        obj = session.execute(
            select(Prediction).where(Prediction.ticker == ticker.upper()).order_by(desc(Prediction.as_of_date)).limit(1)
        ).scalar_one_or_none()
        return _prediction_to_dict(obj) if obj else None


def get_latest_sentiment_for_ticker(ticker: str, days: int = 7) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    with session_scope() as session:
        avg_score = session.execute(
            select(func.avg(NewsSentiment.sentiment_score)).where(
                NewsSentiment.ticker == ticker.upper(),
                NewsSentiment.published_at >= since,
            )
        ).scalar_one_or_none()
        count = session.execute(
            select(func.count(NewsSentiment.id)).where(
                NewsSentiment.ticker == ticker.upper(),
                NewsSentiment.published_at >= since,
            )
        ).scalar_one()
        return {"ticker": ticker.upper(), "sentiment_score": float(avg_score or 0.0), "news_count": int(count or 0)}


def get_latest_market_snapshot(ticker: str) -> dict | None:
    with session_scope() as session:
        obj = session.execute(
            select(MarketPrice).where(MarketPrice.ticker == ticker.upper()).order_by(desc(MarketPrice.date)).limit(1)
        ).scalar_one_or_none()
        if not obj:
            return None
        return {
            "ticker": obj.ticker,
            "date": obj.date.isoformat(),
            "close": obj.close,
            "volume": obj.volume,
            "source": obj.source,
        }


def get_assets() -> list[str]:
    with session_scope() as session:
        return list(session.execute(select(MarketPrice.ticker).distinct().order_by(MarketPrice.ticker)).scalars().all())


def _prediction_to_dict(obj: Prediction | None):
    if obj is None:
        return None
    return {
        "ticker": obj.ticker,
        "as_of_date": obj.as_of_date.isoformat(),
        "probability_favorable": round(float(obj.probability_favorable), 6),
        "probability_pct": round(float(obj.probability_favorable) * 100, 2),
        "sentiment_score": None if obj.sentiment_score is None else round(float(obj.sentiment_score), 6),
        "model_version": obj.model_version,
        "horizon_days": obj.horizon_days,
        "rank_position": obj.rank_position,
    }
