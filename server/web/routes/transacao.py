from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/transacao")
def transacao_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="transacao.html",
        context={
            "request": request,
            "active_page": "transacao",
            "dashboard_label": "Nova transferencia",
        },
    )
