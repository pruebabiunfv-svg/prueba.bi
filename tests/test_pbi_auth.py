import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402


def test_pbi_requires_key_when_configured():
    old = Config.PBI_API_KEY
    Config.PBI_API_KEY = "test-secret"
    try:
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        denied = client.get("/api/pbi/dashboard")
        assert denied.status_code == 401

        allowed = client.get("/api/pbi/dashboard?api_key=test-secret")
        assert allowed.status_code == 200
    finally:
        Config.PBI_API_KEY = old
