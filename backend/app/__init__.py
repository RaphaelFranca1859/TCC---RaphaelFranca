"""Fabrica da aplicacao Flask (camada de Aplicacao da arquitetura em quatro camadas)."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .ingestion import MAX_BYTES
from .store import SessionStore, create_config_store


def create_app(test_config: dict | None = None) -> Flask:
    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    app = Flask(__name__, static_folder=None)
    app.config.update(
        MAX_CONTENT_LENGTH=MAX_BYTES + 1024 * 1024,
        MONGO_URI=os.environ.get("MONGO_URI"),
        DATA_DIR=os.environ.get("DATA_DIR", str(Path(__file__).resolve().parents[1] / "data")),
        SESSION_TTL=int(os.environ.get("SESSION_TTL", 7200)),
    )
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.extensions["sessions"] = SessionStore(ttl_seconds=app.config["SESSION_TTL"])
    app.extensions["configs"] = app.config.get("CONFIG_STORE") or create_config_store(
        app.config["MONGO_URI"], app.config["DATA_DIR"])

    from .api import bp
    app.register_blueprint(bp, url_prefix="/api")

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error=f"O arquivo excede o limite de {MAX_BYTES // (1024 * 1024)} MB."), 413

    if dist.exists():  # serve a interface compilada quando disponivel (implantacao em uma unica origem)
        @app.get("/")
        @app.get("/<path:path>")
        def spa(path: str = ""):
            target = dist / path
            if path and target.is_file():
                return send_from_directory(dist, path)
            return send_from_directory(dist, "index.html")
    return app
