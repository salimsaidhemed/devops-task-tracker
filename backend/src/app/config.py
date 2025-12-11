import os

class BaseConfig:
    APP_NAME = "devops-task-tracker" # TODO: Define Configmap
    SECRET_KEY = os.getenv("SECRET_KEY", "changeme") # TODO: Define Configmap
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/tasks") # TODO: Define Configmap
    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0") # TODO: Define Configmap
    APP_ENV = os.getenv("APP_ENV", "dev") # TODO: Define Configmap


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False


def get_config(name: str | None):
    if name is None:
        name = os.getenv("FLASK_ENV", "dev")

    mapping = {
        "dev": DevConfig,
        "development": DevConfig,
        "prod": ProdConfig,
        "production": ProdConfig,
    }
    return mapping.get(name, DevConfig)