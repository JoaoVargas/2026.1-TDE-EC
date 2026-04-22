from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/investimentos")
def investimentos_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="investimentos.html",
        context={
            "request": request,
            "active_page": "investimentos",
            "dashboard_label": "Minha carteira",
        },
    )


@router.get("/investimentos/distribuicao")
def investimentos_distribuicao_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="investimentos_distribuicao.html",
        context={
            "request": request,
            "active_page": "investimentos",
            "dashboard_label": "Analise de distribuicao",
        },
    )
