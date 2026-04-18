import os
from typing import Generator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


def _build_database_url() -> str:
    explicit_url = os.getenv("DB_URL")
    if explicit_url:
        return explicit_url

    host = os.getenv("DB_HOST", "localhost")
    user = os.getenv("DB_USER", "user")
    password = quote_plus(os.getenv("DB_PASSWORD", "password"))
    database = os.getenv("DB_NAME", "bancodigital")
    port = int(os.getenv("DB_PORT", "3306"))

    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_orm() -> None:
    from models import orm_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
