from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.account_repository import AccountRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


@router.get("/home")
def home_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    accounts = AccountRepository.get_by_user_id(db, user.id)
    account = accounts[0] if accounts else None

    flash = request.query_params.get("flash")

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "active_page": "home",
            "dashboard_label": "Painel financeiro",
            "user": user,
            "account": account,
            "flash": flash,
        },
    )
