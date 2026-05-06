import os
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Banco Digital"
    debug: bool = False

    db_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "user"
    db_password: str = "password"
    db_name: str = "bancodigital"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    session_secret: str = "change-me-in-production"
    session_timeout_seconds: int = 30

    @property
    def database_url(self) -> str:
        if self.db_url:
            return self.db_url
        encoded_password = quote_plus(self.db_password)
        return (
            f"mysql+mysqlconnector://{self.db_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Banco Digital"),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        db_url=os.getenv("DB_URL"),
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_user=os.getenv("DB_USER", "user"),
        db_password=os.getenv("DB_PASSWORD", "password"),
        db_name=os.getenv("DB_NAME", "bancodigital"),
        db_echo=os.getenv("DB_ECHO", "false").lower() in {"1", "true", "yes", "on"},
        db_pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        db_max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        db_pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        db_pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        session_secret=os.getenv("SESSION_SECRET", "change-me-in-production"),
        session_timeout_seconds=int(os.getenv("SESSION_TIMEOUT_SECONDS", "30")),
    )
