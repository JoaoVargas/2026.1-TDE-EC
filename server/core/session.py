from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

SESSION_COOKIE_NAME = "session_id"


def _timeout() -> int:
    from server.core.settings import get_settings
    return get_settings().session_timeout_seconds


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def get_session_user_id(request: Request, db) -> int | None:
    from server.repositories.session_repository import SessionRepository

    token = get_session_token(request)
    if not token:
        return None
    return SessionRepository.get_user_id(db, token)


def set_session_user(
    response: Response,
    db,
    user_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    from server.repositories.session_repository import SessionRepository

    timeout = _timeout()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=timeout)
    token = SessionRepository.create(db, user_id, expires_at, ip_address, user_agent)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=timeout,
    )


def clear_session(request: Request, response: Response, db) -> None:
    from server.repositories.session_repository import SessionRepository

    token = get_session_token(request)
    if token:
        SessionRepository.delete(db, token)
    response.delete_cookie(SESSION_COOKIE_NAME)
