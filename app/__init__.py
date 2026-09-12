from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.db import init_db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Idempotente; crea tablas si no existen. Para migraciones complejas usar Alembic.
    init_db()

    from app.routes import api
    app.register_blueprint(api)

    @app.get("/")
    def root():
        return jsonify({
            "name": Config.APP_NAME,
            "status": "running",
            "endpoints": [
                "/api/health",
                "/api/dashboard",
                "/api/assets",
                "/api/predict/<ticker>",
                "/api/sentiment/<ticker>",
                "/api/pbi/dashboard",
                "/api/pbi/history",
            ],
        })

    return app
