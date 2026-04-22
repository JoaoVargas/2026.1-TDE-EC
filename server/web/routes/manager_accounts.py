from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/manager/accounts")
def manager_accounts_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="manager_accounts.html",
        context={
            "request": request,
            "active_page": "manager",
            "dashboard_label": "Gestao de usuarios e contas",
            "show_sidebar": False,
        },
    )
