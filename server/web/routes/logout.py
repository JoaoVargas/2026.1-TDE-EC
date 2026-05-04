from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from server.core.session import clear_session

router = APIRouter(tags=["pages"])


@router.post("/logout")
def logout(request: Request):
    clear_session(request)
    return RedirectResponse("/login", status_code=302)
