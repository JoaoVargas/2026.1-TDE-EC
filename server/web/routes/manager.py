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
            "active_page": "manager",
            "dashboard_label": "Central de gerencia",
            "show_sidebar": False,
        },
    )
