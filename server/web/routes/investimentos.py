import json
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.models.transaction import TransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.portfolio_price_history_repository import PortfolioPriceHistoryRepository
from server.repositories.portfolio_repository import PortfolioRepository
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.user_portfolio_repository import UserPortfolioRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])

_CLASS_COLORS = {
    "Renda fixa": "#2eb8b8",
    "Renda variavel": "#22888c",
    "Criptomoedas": "#c8922a",
}
_DEFAULT_COLOR = "#6fd0ce"


def _fmt(value: Decimal) -> str:
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _build_holdings(db, user_id: int):
    user_portfolios = UserPortfolioRepository.get_by_user_id(db, user_id)
    all_portfolios = {p.id: p for p in PortfolioRepository.list_all(db)}

    total = Decimal("0")
    holdings = []
    class_totals: dict[str, Decimal] = {}

    for up in user_portfolios:
        portfolio = all_portfolios.get(up.portfolio_id)
        if not portfolio:
            continue
        value = portfolio.stock_price * up.stock_amount
        total += value
        class_totals[portfolio.name] = class_totals.get(portfolio.name, Decimal("0")) + value
        holdings.append({
            "id": portfolio.id,
            "name": portfolio.stock_name,
            "class": portfolio.name,
            "stock_code": portfolio.stock_code,
            "amount": up.stock_amount,
            "price": portfolio.stock_price,
            "value": value,
            "value_str": _fmt(value),
        })

    return total, holdings, class_totals


def _build_chart_json(total: Decimal, holdings: list[dict], class_totals: dict[str, Decimal]) -> str:
    classes = [
        {
            "label": cls,
            "value": float(val),
            "color": _CLASS_COLORS.get(cls, _DEFAULT_COLOR),
        }
        for cls, val in class_totals.items()
    ]
    assets = [
        {
            "name": h["name"],
            "className": h["class"],
            "value": float(h["value"]),
        }
        for h in holdings
    ]
    return json.dumps({"classes": classes, "assets": assets, "total": float(total)})


def _price_history_json(db, portfolio_id: int) -> str:
    records = PortfolioPriceHistoryRepository.get_by_portfolio_id(db, portfolio_id)
    return json.dumps([float(r.price) for r in records])


def _build_resumo_json(db, holdings: list[dict]) -> str:
    if not holdings:
        return json.dumps({"labels": [], "portfolios": [], "total": []})

    portfolio_lines = []
    shared_labels: list[str] | None = None

    for h in holdings:
        records = PortfolioPriceHistoryRepository.get_by_portfolio_id(db, h["id"])
        if not records:
            continue
        prices = [float(r.price) for r in records]
        values = [p * float(h["amount"]) for p in prices]
        dates = [r.recorded_at.strftime("%d/%m") for r in records]
        if shared_labels is None:
            shared_labels = dates
        portfolio_lines.append({
            "name": f"{h['name']} ({h['stock_code']})",
            "class": h["class"],
            "color": _CLASS_COLORS.get(h["class"], _DEFAULT_COLOR),
            "values": values,
        })

    if not portfolio_lines:
        return json.dumps({"labels": [], "portfolios": [], "total": []})

    n = len(shared_labels)
    total = [sum(p["values"][i] if i < len(p["values"]) else 0 for p in portfolio_lines) for i in range(n)]

    return json.dumps({"labels": shared_labels, "portfolios": portfolio_lines, "total": total})


_ERROR_MAP = {
    "saldo_insuficiente": "Saldo insuficiente para esta operação.",
    "valor_invalido": "Valor inválido.",
    "sem_conta": "Conta corrente não encontrada.",
    "portfolio_nao_encontrado": "Carteira não encontrada.",
    "cotas_insuficientes": "Você não possui cotas suficientes para retirar esse valor.",
}

_FLASH_MAP = {
    "deposito_realizado": "Investimento realizado com sucesso!",
    "resgate_realizado": "Resgate realizado com sucesso!",
}


@router.get("/investimentos")
def investimentos_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    total, holdings, class_totals = _build_holdings(db, user.id)

    fixo = class_totals.get("Renda fixa", Decimal("0"))
    variavel = class_totals.get("Renda variavel", Decimal("0"))

    for h in holdings:
        h["price_history_json"] = _price_history_json(db, h["id"])

    # All available portfolios with user's current position
    user_positions = {up.portfolio_id: up for up in UserPortfolioRepository.get_by_user_id(db, user.id)}
    all_portfolios = PortfolioRepository.list_all(db)
    available = [
        {
            "id": p.id,
            "name": p.name,
            "stock_code": p.stock_code,
            "stock_name": p.stock_name,
            "price_str": _fmt(p.stock_price),
            "price_cents": int(p.stock_price * 100),
            "has_position": p.id in user_positions,
            "amount": user_positions[p.id].stock_amount if p.id in user_positions else Decimal("0"),
            "price_history_json": _price_history_json(db, p.id),
        }
        for p in all_portfolios
    ]

    account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)

    return templates.TemplateResponse(
        request=request,
        name="investimentos.html",
        context={
            "request": request,
            "active_page": "investimentos",
            "dashboard_label": "Minha carteira",
            "user": user,
            "total_str": _fmt(total),
            "fixo_str": _fmt(fixo),
            "variavel_str": _fmt(variavel),
            "holdings": holdings,
            "available": available,
            "balance_str": _fmt(account.balance) if account else "0,00",
            "balance_cents": int(account.balance * 100) if account else 0,
            "error": _ERROR_MAP.get(request.query_params.get("error")),
            "flash": _FLASH_MAP.get(request.query_params.get("flash")),
        },
    )


@router.post("/investimentos/{portfolio_id}/depositar")
async def investimentos_depositar(
    portfolio_id: int,
    request: Request,
    amount_cents: int = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    portfolio = PortfolioRepository.get_by_id(db, portfolio_id)
    if not portfolio:
        return RedirectResponse("/investimentos?error=portfolio_nao_encontrado", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse("/investimentos?error=valor_invalido", status_code=302)

    account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    if not account:
        return RedirectResponse("/investimentos?error=sem_conta", status_code=302)

    if account.balance < amount:
        return RedirectResponse("/investimentos?error=saldo_insuficiente", status_code=302)

    shares = amount / portfolio.stock_price

    cursor = db.cursor()
    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account.id))
    cursor.close()

    TransactionRepository.create(
        db,
        type=TransactionType.EXPENSE,
        from_account_id=account.id,
        to_account_id=None,
        amount=amount,
        description=f"Investimento em {portfolio.stock_name} ({portfolio.stock_code})",
    )

    existing = UserPortfolioRepository.get_by_user_and_portfolio(db, user.id, portfolio_id)
    if existing:
        UserPortfolioRepository.update_amount(db, user_portfolio_id=existing.id, stock_amount=existing.stock_amount + shares)
    else:
        UserPortfolioRepository.create(db, portfolio_id=portfolio_id, user_id=user.id, stock_amount=shares)

    db.commit()
    return RedirectResponse("/investimentos?flash=deposito_realizado", status_code=302)


@router.post("/investimentos/{portfolio_id}/retirar")
async def investimentos_retirar(
    portfolio_id: int,
    request: Request,
    shares_str: str = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    portfolio = PortfolioRepository.get_by_id(db, portfolio_id)
    if not portfolio:
        return RedirectResponse("/investimentos?error=portfolio_nao_encontrado", status_code=302)

    try:
        shares = Decimal(shares_str.replace(",", "."))
        if shares <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError):
        return RedirectResponse("/investimentos?error=valor_invalido", status_code=302)

    existing = UserPortfolioRepository.get_by_user_and_portfolio(db, user.id, portfolio_id)
    if not existing or existing.stock_amount < shares:
        return RedirectResponse("/investimentos?error=cotas_insuficientes", status_code=302)

    amount = shares * portfolio.stock_price

    account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    if not account:
        return RedirectResponse("/investimentos?error=sem_conta", status_code=302)

    cursor = db.cursor()
    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account.id))
    cursor.close()

    TransactionRepository.create(
        db,
        type=TransactionType.DEPOSIT,
        from_account_id=None,
        to_account_id=account.id,
        amount=amount,
        description=f"Resgate de {portfolio.stock_name} ({portfolio.stock_code})",
    )

    new_amount = existing.stock_amount - shares
    if new_amount <= Decimal("0.0001"):
        UserPortfolioRepository.delete(db, user_portfolio_id=existing.id)
    else:
        UserPortfolioRepository.update_amount(db, user_portfolio_id=existing.id, stock_amount=new_amount)

    db.commit()
    return RedirectResponse("/investimentos?flash=resgate_realizado", status_code=302)


@router.get("/investimentos/resumo")
def investimentos_resumo_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    total, holdings, class_totals = _build_holdings(db, user.id)
    fixo = class_totals.get("Renda fixa", Decimal("0"))
    variavel = class_totals.get("Renda variavel", Decimal("0"))
    chart_json = _build_resumo_json(db, holdings)

    return templates.TemplateResponse(
        request=request,
        name="investimentos_resumo.html",
        context={
            "request": request,
            "active_page": "investimentos",
            "dashboard_label": "Resumo dos investimentos",
            "user": user,
            "total_str": _fmt(total),
            "fixo_str": _fmt(fixo),
            "variavel_str": _fmt(variavel),
            "chart_json": chart_json,
        },
    )


@router.get("/investimentos/distribuicao")
def investimentos_distribuicao_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    total, holdings, class_totals = _build_holdings(db, user.id)

    fixo = class_totals.get("Renda fixa", Decimal("0"))
    variavel = class_totals.get("Renda variavel", Decimal("0"))
    chart_json = _build_chart_json(total, holdings, class_totals)

    return templates.TemplateResponse(
        request=request,
        name="investimentos_distribuicao.html",
        context={
            "request": request,
            "active_page": "investimentos",
            "dashboard_label": "Análise de distribuição",
            "user": user,
            "total_str": _fmt(total),
            "fixo_str": _fmt(fixo),
            "variavel_str": _fmt(variavel),
            "chart_json": chart_json,
        },
    )
