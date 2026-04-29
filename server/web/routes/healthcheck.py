from fastapi import APIRouter, Request

from server.db.connection import check_database_connection
from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/healthcheck")
def healthcheck_page(request: Request):
    db_status = "ok"
    db_error = ""

    try:
        check_database_connection()
    except RuntimeError as exc:
        db_status = "error"
        db_error = str(exc)

    return templates.TemplateResponse(
        request=request,
        name="healthcheck.html",
        context={
            "request": request,
            "api_status": "ok",
            "db_status": db_status,
            "db_error": db_error,
        },
    )
