from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/home")
def home_alias_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "active_page": "home", "dashboard_label": "Painel financeiro"},
    )
