from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.user import UserType
from server.repositories.account_repository import AccountRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])


@router.get("/manager")
def manager_page(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    total_users = UserRepository.count_all(db)
    total_managers = UserRepository.count_by_type(db, UserType.MANAGER)
    total_accounts = AccountRepository.count_all(db)

    return templates.TemplateResponse(
        request=request,
        name="manager.html",
        context={
            "request": request,
            "active_page": "manager_dashboard",
            "dashboard_label": "Painel de gerência",
            "sidebar_template": "components/manager_sidebar.html",
            "user": user,
            "total_users": total_users,
            "total_managers": total_managers,
            "total_accounts": total_accounts,
        },
    )
