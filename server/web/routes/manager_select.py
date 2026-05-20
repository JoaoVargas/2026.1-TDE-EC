from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])


@router.get("/manager/select")
def manager_select_page(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    return templates.TemplateResponse(
        request=request,
        name="manager_select.html",
        context={
            "request": request,
            "active_page": "manager_select",
            "dashboard_label": "Selecione seu acesso",
            "show_sidebar": False,
            "user": user,
        },
    )
