from fastapi import Request

SESSION_KEY = "user_id"


def get_session_user_id(request: Request) -> int | None:
    return request.session.get(SESSION_KEY)


def set_session_user(request: Request, user_id: int) -> None:
    request.session[SESSION_KEY] = user_id


def clear_session(request: Request) -> None:
    request.session.clear()
