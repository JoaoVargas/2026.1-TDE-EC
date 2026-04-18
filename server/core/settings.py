import os
from functools import lru_cache
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Banco Digital API"
    debug: bool = False
    cors_allow_origins: list[str] = ["*"]

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
    cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    cors_allow_origins = [origin.strip() for origin in cors_raw.split(",") if origin]

    return Settings(
        app_name=os.getenv("APP_NAME", "Banco Digital API"),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"},
        cors_allow_origins=cors_allow_origins or ["*"],
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
    )
