from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/extrato")
def extrato_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="extrato.html",
        context={"request": request, "active_page": "extrato", "dashboard_label": "Extrato"},
    )
