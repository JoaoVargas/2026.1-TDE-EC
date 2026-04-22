from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/cadastro")
def cadastro_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cadastro.html",
        context={"request": request},
    )
