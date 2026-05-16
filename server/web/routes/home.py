from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.repositories.account_repository import AccountRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


@router.get("/home")
def home_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)

    flash = request.query_params.get("flash")

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "active_page": "home",
            "dashboard_label": "Painel financeiro",
            "user": user,
            "checking_account": checking_account,
            "savings_account": savings_account,
            "flash": flash,
        },
    )