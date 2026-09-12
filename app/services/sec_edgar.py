from datetime import datetime
import requests
from app.config import Config

# CIKs de los activos empresariales iniciales. ETFs se omiten.
CIK_MAP = {
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
}

METRIC_MAP = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
    "net_income": ["NetIncomeLoss"],
    "assets": ["Assets"],
}


def fetch_company_fundamentals(ticker: str) -> list[dict]:
    ticker = ticker.upper()
    cik = CIK_MAP.get(ticker)
    if not cik:
        return []

    headers = {
        "User-Agent": Config.SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=headers, timeout=45)
    response.raise_for_status()
    payload = response.json()
    us_gaap = payload.get("facts", {}).get("us-gaap", {})

    rows = []
    for metric_name, candidate_tags in METRIC_MAP.items():
        fact = next((us_gaap.get(tag) for tag in candidate_tags if us_gaap.get(tag)), None)
        if not fact:
            continue
        units = fact.get("units", {})
        values = units.get("USD") or next(iter(units.values()), [])
        valid = [v for v in values if v.get("val") is not None and v.get("end")]
        # Preferir reportes 10-K/10-Q y el dato mas reciente.
        valid = [v for v in valid if v.get("form") in {"10-K", "10-Q"}] or valid
        if not valid:
            continue
        latest = max(valid, key=lambda v: (v.get("end", ""), v.get("filed", "")))
        rows.append({
            "ticker": ticker,
            "as_of_date": datetime.strptime(latest["end"], "%Y-%m-%d").date(),
            "metric": metric_name,
            "value": float(latest["val"]),
            "unit": "USD",
            "source": "sec_edgar",
        })
    return rows
