import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    env: str
    host: str
    port: int
    db_path: str
    jwt_secret: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        env=os.environ.get("YGNT_WEB_ENV", "development"),
        host=os.environ.get("YGNT_WEB_HOST", "127.0.0.1"),
        port=int(os.environ.get("YGNT_WEB_PORT", "8000")),
        db_path=os.environ.get("YGNT_WEB_DB_PATH", "data/ygnt_web.sqlite3"),
        # Valeur de repli utilisable uniquement en développement local :
        # toute mise en ligne doit définir YGNT_WEB_JWT_SECRET explicitement.
        jwt_secret=os.environ.get(
            "YGNT_WEB_JWT_SECRET", "dev-insecure-secret-change-me-in-every-real-environment"
        ),
    )
