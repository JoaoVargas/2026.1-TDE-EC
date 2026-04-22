from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/manager/select")
def manager_select_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="manager_select.html",
        context={
            "request": request,
            "active_page": "manager_select",
            "dashboard_label": "Selecione seu acesso",
            "show_sidebar": False,
        },
    )
