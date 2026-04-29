from typing import Generator

import mysql.connector
import mysql.connector.pooling

from server.core.settings import get_settings

_pool: mysql.connector.pooling.MySQLConnectionPool | None = None


def _get_pool() -> mysql.connector.pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="bancodigital",
            pool_size=settings.db_pool_size,
            pool_timeout=settings.db_pool_timeout,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
        )
    return _pool


def get_db() -> Generator:
    conn = _get_pool().get_connection()
    try:
        yield conn
    finally:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()


def check_database_connection() -> None:
    try:
        conn = _get_pool().get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
    except Exception as exc:
        raise RuntimeError("Database connection check failed") from exc
