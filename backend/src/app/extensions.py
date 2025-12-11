import os
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()
redis_client: Redis | None = None

def init_redis(app=None) -> None:
    """
    Initialize a global Redis client from app config or env.
    Safe to call multiple times.
    """
    global redis_client

    if redis_client is not None:
        return

    if app is not None and "REDIS_URL" in app.config:
        url = app.config["REDIS_URL"]
    else:
        url = os.getenv("REDIS_URL", "redis://redis:6379/0") #TODO : get from configmap

    redis_client = Redis.from_url(url, decode_responses=True)