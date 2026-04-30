import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.portfolio_repository import PortfolioRepository
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


@router.get("/investimentos")
def investimentos_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    total, holdings, class_totals = _build_holdings(db, user.id)

    fixo = class_totals.get("Renda fixa", Decimal("0"))
    variavel = class_totals.get("Renda variavel", Decimal("0"))

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
