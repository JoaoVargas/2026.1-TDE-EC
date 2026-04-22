from fastapi import APIRouter, Request

from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )
