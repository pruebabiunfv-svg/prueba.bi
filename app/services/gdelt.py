from datetime import datetime, timezone
import requests
from app.config import Config

COMPANY_QUERY = {
    "AAPL": '"Apple" OR "AAPL"',
    "MSFT": '"Microsoft" OR "MSFT"',
    "NVDA": '"NVIDIA" OR "NVDA"',
    "AMZN": '"Amazon" OR "AMZN"',
    "GOOGL": '"Alphabet" OR "Google" OR "GOOGL"',
    "SPY": '"S&P 500" OR "SPY ETF"',
    "QQQ": '"Nasdaq 100" OR "QQQ ETF"',
}


def fetch_gdelt_news(ticker: str, max_records: int | None = None) -> list[dict]:
    query = COMPANY_QUERY.get(ticker.upper(), ticker.upper())
    max_records = max_records or Config.GDELT_MAX_RECORDS
    response = requests.get(
        "https://api.gdeltproject.org/api/v2/doc/doc",
        params={
            "query": query,
            "mode": "ArtList",
            "maxrecords": max_records,
            "format": "json",
            "sort": "HybridRel",
        },
        timeout=45,
    )
    response.raise_for_status()
    articles = response.json().get("articles", [])
    rows = []
    for article in articles:
        title = (article.get("title") or "").strip()
        if not title:
            continue
        seen = article.get("seendate")
        published = _parse_gdelt_date(seen)
        rows.append({
            "ticker": ticker.upper(),
            "published_at": published,
            "title": title,
            "url": article.get("url"),
            "domain": article.get("domain"),
            "source": "gdelt",
        })
    return rows


def _parse_gdelt_date(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return datetime.now(timezone.utc).replace(tzinfo=None)
