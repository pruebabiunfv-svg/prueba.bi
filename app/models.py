from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text, UniqueConstraint, Index
from app.db import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    source = Column(String(32), default="yahoo")
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("ticker", "date", name="uq_market_ticker_date"),)


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"
    id = Column(Integer, primary_key=True)
    series_id = Column(String(64), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    value = Column(Float)
    source = Column(String(32), default="fred")
    __table_args__ = (UniqueConstraint("series_id", "date", name="uq_macro_series_date"),)


class Fundamental(Base):
    __tablename__ = "fundamentals"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)
    metric = Column(String(64), nullable=False)
    value = Column(Float)
    unit = Column(String(32), default="USD")
    source = Column(String(32), default="sec_edgar")
    __table_args__ = (
        UniqueConstraint("ticker", "as_of_date", "metric", name="uq_fund_ticker_date_metric"),
    )


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    published_at = Column(DateTime, nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text)
    domain = Column(String(255))
    sentiment_label = Column(String(16))
    sentiment_score = Column(Float)
    model_name = Column(String(128))
    inference_source = Column(String(32), default="huggingface")
    source = Column(String(32), default="gdelt")
    __table_args__ = (
        Index("ix_news_ticker_published", "ticker", "published_at"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)
    probability_favorable = Column(Float, nullable=False)
    sentiment_score = Column(Float)
    model_version = Column(String(64), default="xgboost")
    horizon_days = Column(Integer, default=126)
    rank_position = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("ticker", "as_of_date", name="uq_prediction_ticker_date"),)


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), nullable=False, index=True)
    run_date = Column(Date, nullable=False, index=True)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
