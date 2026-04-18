from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from server.db.session import check_database_connection

router = APIRouter(tags=["pages"])

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
def home_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "app_name": "Banco Digital API",
        },
    )


@router.get("/home")
def home_alias_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "active_page": "home", "dashboard_label": "Painel financeiro"},
    )


@router.get("/transacao")
def transacao_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="transacao.html",
        context={"request": request, "active_page": "transacao", "dashboard_label": "Nova transferencia"},
    )


@router.get("/investimentos")
def investimentos_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="investimentos.html",
        context={"request": request, "active_page": "investimentos", "dashboard_label": "Minha carteira"},
    )


@router.get("/investimentos/distribuicao")
def investimentos_distribuicao_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="investimentos_distribuicao.html",
        context={"request": request, "active_page": "investimentos", "dashboard_label": "Analise de distribuicao"},
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )


@router.get("/cadastro")
def cadastro_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cadastro.html",
        context={"request": request},
    )


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
