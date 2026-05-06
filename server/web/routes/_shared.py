from decimal import Decimal
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from server.core.session import SESSION_COOKIE_NAME, get_session_token
from server.models.user import User, UserType

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _format_brl(value) -> str:
    amount = Decimal(str(value)) if not isinstance(value, Decimal) else value
    s = f"{float(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _user_initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    return "".join(p[0].upper() for p in parts[:2]) if parts else "U"


def _is_manager(user: User) -> bool:
    val = user.type.value if hasattr(user.type, "value") else str(user.type)
    return val == UserType.MANAGER.value


templates.env.filters["brl"] = _format_brl
templates.env.globals["user_initials"] = _user_initials
templates.env.globals["is_manager"] = _is_manager


def require_user(request: Request, db) -> User | RedirectResponse:
    from server.repositories.session_repository import SessionRepository
    from server.repositories.user_repository import UserRepository

    token = get_session_token(request)
    if not token:
        return RedirectResponse("/login", status_code=302)

    user_id = SessionRepository.get_user_id(db, token)
    if not user_id:
        response = RedirectResponse("/login", status_code=302)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        SessionRepository.delete(db, token)
        response = RedirectResponse("/login", status_code=302)
        response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    return user


def require_manager(request: Request, db) -> User | RedirectResponse:
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    if not _is_manager(result):
        return RedirectResponse("/home", status_code=302)
    return result
