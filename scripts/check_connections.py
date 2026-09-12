import json
from sqlalchemy import text
from app.config import Config
from app.db import engine
from app.services.huggingface_finbert import classify_financial_text


def main():
    result = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["database"] = "ok"
    except Exception as exc:
        result["database"] = f"error: {exc.__class__.__name__}: {exc}"

    result["huggingface_token"] = "configured" if Config.HF_TOKEN else "missing"
    if Config.HF_TOKEN:
        try:
            s = classify_financial_text("The company reported stronger revenue growth and improved margins.")
            result["huggingface_inference"] = {"status": "ok", "label": s.label, "score": s.score}
        except Exception as exc:
            result["huggingface_inference"] = f"error: {exc}"

    result["fred_key"] = "configured" if Config.FRED_API_KEY else "missing"
    result["alpha_vantage_key"] = "configured" if Config.ALPHA_VANTAGE_API_KEY else "missing"
    result["pbi_api_key"] = "configured" if Config.PBI_API_KEY else "open endpoint"
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
