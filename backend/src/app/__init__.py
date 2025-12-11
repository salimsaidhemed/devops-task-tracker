from flask import Flask
import os

from .config import get_config
from .extensions import db,init_redis
from .routes import api_bp

def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    config_obj = get_config(config_name)
    app.config.from_object(config_obj)

    # Init extensions
    db.init_app(app)
    init_redis(app)
    
       # Auto-create tables in dev/compose if requested
    if os.getenv("AUTO_CREATE_DB") == "1":
        with app.app_context():
            db.create_all()

    # Blueprints
    app.register_blueprint(api_bp, url_prefix="/api")

    # Health endpoints (no auth, no DB required)
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz():
        return {"status": "ready"}

    return app