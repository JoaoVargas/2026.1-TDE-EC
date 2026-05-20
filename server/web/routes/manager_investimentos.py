import json
import ssl
import urllib.request
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.models.transaction import TransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.manager_portfolio_repository import ManagerPortfolioRepository
from server.repositories.portfolio_repository import PortfolioRepository
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.user_portfolio_repository import UserPortfolioRepository
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])

_PORTFOLIO_CLASSES = ["Renda fixa", "Renda variavel", "Criptomoedas"]

_FEEDBACK_MAP = {
    "carteira_criada": "Carteira criada com sucesso.",
    "carteira_deletada": "Carteira encerrada. Todos os investidores foram reembolsados.",
    "carteira_nao_encontrada": "Carteira não encontrada.",
    "cotacao_atualizada": "Cotação atualizada com sucesso.",
    "cotacao_erro": "Não foi possível obter a cotação para esse ativo. Verifique o código.",
    "campos_invalidos": "Preencha todos os campos corretamente.",
}


def _http_get(url: str) -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; BetaBank/1.0)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
        return json.loads(resp.read())


def _fetch_stock_price(stock_code: str) -> Decimal | None:
    # Tenta brapi.dev primeiro (bolsa brasileira)
    try:
        data = _http_get(f"https://brapi.dev/api/quote/{stock_code}?token=demo")
        price = data["results"][0]["regularMarketPrice"]
        return Decimal(str(price))
    except Exception:
        pass

    # Fallback: Yahoo Finance (adiciona .SA para B3)
    try:
        ticker = stock_code if "." in stock_code else f"{stock_code}.SA"
        data = _http_get(
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
            "?interval=1d&range=1d"
        )
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return Decimal(str(price))
    except Exception:
        pass

    return None


@router.get("/manager/investimentos")
def manager_investimentos_page(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    manager = result

    portfolios = PortfolioRepository.list_all(db)

    return templates.TemplateResponse(
        request=request,
        name="manager_investimentos.html",
        context={
            "request": request,
            "active_page": "manager_investimentos",
            "dashboard_label": "Gestão de investimentos",
            "sidebar_template": "components/manager_sidebar.html",
            "user": manager,
            "portfolios": portfolios,
            "classes": _PORTFOLIO_CLASSES,
            "feedback": _FEEDBACK_MAP.get(request.query_params.get("feedback")),
        },
    )


@router.post("/manager/investimentos/criar")
async def manager_criar_carteira(
    request: Request,
    name: str = Form(...),
    stock_code: str = Form(...),
    stock_name: str = Form(...),
    stock_price: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    manager = result

    name = name.strip()
    stock_code = stock_code.strip().upper()
    stock_name = stock_name.strip()

    if not name or not stock_code or not stock_name:
        return RedirectResponse("/manager/investimentos?feedback=campos_invalidos", status_code=302)

    try:
        price = Decimal(stock_price.replace(",", "."))
        if price <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        return RedirectResponse("/manager/investimentos?feedback=campos_invalidos", status_code=302)

    portfolio = PortfolioRepository.create(
        db, name=name, stock_code=stock_code, stock_name=stock_name, stock_price=price
    )
    ManagerPortfolioRepository.create(db, portfolio_id=portfolio.id, manager_id=manager.id)
    db.commit()
    return RedirectResponse("/manager/investimentos?feedback=carteira_criada", status_code=302)


@router.post("/manager/investimentos/{portfolio_id}/cotacao")
async def manager_atualizar_cotacao(
    portfolio_id: int,
    request: Request,
    stock_price: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    portfolio = PortfolioRepository.get_by_id(db, portfolio_id)
    if not portfolio:
        return RedirectResponse("/manager/investimentos?feedback=cotacao_erro", status_code=302)

    try:
        new_price = Decimal(stock_price.replace(",", "."))
        if new_price <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        return RedirectResponse("/manager/investimentos?feedback=campos_invalidos", status_code=302)

    PortfolioRepository.update_price(db, portfolio_id=portfolio_id, stock_price=new_price)
    db.commit()
    return RedirectResponse("/manager/investimentos?feedback=cotacao_atualizada", status_code=302)


@router.get("/manager/investimentos/{portfolio_id}/cotacao-api")
def manager_buscar_cotacao_api(portfolio_id: int, request: Request, db=Depends(get_db)):
    """Endpoint JSON usado pelo JS para buscar cotação da API externa."""
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return {"error": "não autorizado"}

    portfolio = PortfolioRepository.get_by_id(db, portfolio_id)
    if not portfolio:
        return {"error": "carteira não encontrada"}

    price = _fetch_stock_price(portfolio.stock_code)
    if price is None:
        return {"error": "cotação não disponível"}

    return {"price": str(price)}


@router.post("/manager/investimentos/{portfolio_id}/deletar")
async def manager_deletar_carteira(
    portfolio_id: int,
    request: Request,
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    portfolio = PortfolioRepository.get_by_id(db, portfolio_id)
    if not portfolio:
        return RedirectResponse("/manager/investimentos?feedback=carteira_nao_encontrada", status_code=302)

    user_positions = UserPortfolioRepository.get_by_portfolio_id(db, portfolio_id)
    for up in user_positions:
        account = AccountRepository.get_by_user_and_type(db, up.user_id, AccountType.CHECKING)
        if not account:
            continue
        refund = up.stock_amount * portfolio.stock_price
        cursor = db.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (refund, account.id))
        cursor.close()
        TransactionRepository.create(
            db,
            type=TransactionType.DEPOSIT,
            from_account_id=None,
            to_account_id=account.id,
            amount=refund,
            description=f"Reembolso pelo encerramento da carteira {portfolio.stock_name} ({portfolio.stock_code})",
        )

    UserPortfolioRepository.delete_by_portfolio_id(db, portfolio_id=portfolio_id)
    ManagerPortfolioRepository.delete_by_portfolio_id(db, portfolio_id=portfolio_id)
    PortfolioRepository.delete(db, portfolio_id=portfolio_id)
    db.commit()

    return RedirectResponse("/manager/investimentos?feedback=carteira_deletada", status_code=302)
