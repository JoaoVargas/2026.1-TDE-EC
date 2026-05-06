from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from server.core.session import SESSION_COOKIE_NAME
from server.core.settings import get_settings
from server.db.connection import _get_pool, check_database_connection
from server.db.init_db import init_db
from server.web.router import web_router


class SessionRefreshMiddleware(BaseHTTPMiddleware):
    """Sliding-window inactivity timeout: refreshes expires_at and cookie max_age on every authenticated request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not token:
            return response

        try:
            from server.repositories.session_repository import SessionRepository

            settings = get_settings()
            db_conn = _get_pool().get_connection()
            try:
                user_id = SessionRepository.get_user_id(db_conn, token)
                if user_id:
                    timeout = settings.session_timeout_seconds
                    new_expires = datetime.utcnow() + timedelta(seconds=timeout)
                    SessionRepository.refresh(db_conn, token, new_expires)
                    response.set_cookie(
                        key=SESSION_COOKIE_NAME,
                        value=token,
                        httponly=True,
                        samesite="lax",
                        max_age=timeout,
                    )
            finally:
                db_conn.close()
        except Exception:
            pass

        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_database_connection()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    base_dir = Path(__file__).resolve().parents[1]

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(SessionRefreshMiddleware)
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
    app.include_router(web_router)
    return app
