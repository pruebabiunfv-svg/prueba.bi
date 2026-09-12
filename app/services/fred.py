from datetime import datetime
import requests
from app.config import Config

DEFAULT_SERIES = ["CPIAUCSL", "FEDFUNDS", "UNRATE"]


def fetch_fred_series(series_id: str) -> list[dict]:
    if not Config.FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY no esta configurado")

    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": Config.FRED_API_KEY,
            "file_type": "json",
            "sort_order": "asc",
        },
        timeout=45,
    )
    response.raise_for_status()
    observations = response.json().get("observations", [])
    rows = []
    for obs in observations:
        if obs.get("value") in (None, "."):
            continue
        rows.append({
            "series_id": series_id,
            "date": datetime.strptime(obs["date"], "%Y-%m-%d").date(),
            "value": float(obs["value"]),
            "source": "fred",
        })
    return rows
