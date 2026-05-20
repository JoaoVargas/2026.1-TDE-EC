from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.core.session import clear_session
from server.db.connection import get_db

router = APIRouter(tags=["pages"])


@router.post("/logout")
def logout(request: Request, db=Depends(get_db)):
    response = RedirectResponse("/login", status_code=302)
    clear_session(request, response, db)
    return response
