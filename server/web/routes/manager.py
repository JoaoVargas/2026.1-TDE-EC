from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/manager")
def manager_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="manager.html",
        context={
            "request": request,
            "active_page": "manager_dashboard",
            "dashboard_label": "Painel de gerencia",
            "sidebar_template": "components/manager_sidebar.html",
        },
    )
