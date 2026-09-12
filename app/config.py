import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "y", "on"}


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///local_inversion_bi.db")
    # Railway MySQL suele entregar mysql://...; SQLAlchemy + PyMySQL usa mysql+pymysql://...
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://"):]
    return url


class Config:
    APP_NAME = os.getenv("APP_NAME", "Business Analytics - Inversiones a Largo Plazo")
    DATABASE_URL = _database_url()
    DEMO_MODE = _bool("DEMO_MODE", False)
    TICKERS = [t.strip().upper() for t in os.getenv(
        "TICKERS", "AAPL,MSFT,NVDA,AMZN,GOOGL,SPY,QQQ"
    ).split(",") if t.strip()]
    MARKET_PERIOD = os.getenv("MARKET_PERIOD", "5y")
    PREDICTION_HORIZON_DAYS = int(os.getenv("PREDICTION_HORIZON_DAYS", "126"))

    HF_TOKEN = os.getenv("HF_TOKEN", "")
    HF_MODEL = os.getenv("HF_MODEL", "ProsusAI/finbert")
    HF_PROVIDER = os.getenv("HF_PROVIDER", "hf-inference")
    HF_TIMEOUT_SECONDS = float(os.getenv("HF_TIMEOUT_SECONDS", "45"))
    HF_ALLOW_NEUTRAL_FALLBACK = _bool("HF_ALLOW_NEUTRAL_FALLBACK", False)

    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FRED_API_KEY = os.getenv("FRED_API_KEY", "")
    SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "Proyecto universitario contacto@example.com")
    GDELT_MAX_RECORDS = int(os.getenv("GDELT_MAX_RECORDS", "25"))

    PBI_API_KEY = os.getenv("PBI_API_KEY", "")

    MODEL_PATH = Path(os.getenv("MODEL_PATH", str(ROOT_DIR / "models" / "xgb_model.joblib")))
    MODEL_META_PATH = Path(os.getenv("MODEL_META_PATH", str(ROOT_DIR / "models" / "xgb_model_meta.json")))
