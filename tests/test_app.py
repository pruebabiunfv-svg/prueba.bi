import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app  # noqa: E402


def test_root_and_health():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    root = client.get("/")
    assert root.status_code == 200
    assert root.get_json()["status"] == "running"

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["database"] == "ok"
    
    
