from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.repositories.account_repository import AccountRepository
from server.repositories.credit_card_repository import CreditCardRepository
from server.repositories.portfolio_repository import PortfolioRepository
from server.repositories.user_portfolio_repository import UserPortfolioRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


def _fmt(value: Decimal) -> str:
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _get_investment_summary(db, user_id: int, checking_account):
    user_portfolios = UserPortfolioRepository.get_by_user_id(db, user_id)
    if not user_portfolios:
        return None

    all_portfolios = {p.id: p for p in PortfolioRepository.list_all(db)}
    total = Decimal("0")
    for up in user_portfolios:
        portfolio = all_portfolios.get(up.portfolio_id)
        if portfolio:
            total += portfolio.stock_price * up.stock_amount

    if total == 0:
        return None

    net_invested = Decimal("0")
    if checking_account:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE from_account_id = %s AND type = 'expense' AND description LIKE 'Investimento em%%'",
            (checking_account.id,),
        )
        invested = Decimal(str(cursor.fetchone()["total"]))
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE to_account_id = %s AND type = 'deposit' AND description LIKE 'Resgate de%%'",
            (checking_account.id,),
        )
        withdrawn = Decimal(str(cursor.fetchone()["total"]))
        cursor.close()
        net_invested = invested - withdrawn

    change = total - net_invested
    change_pct = float(change / net_invested * 100) if net_invested > 0 else 0.0

    return {
        "total_str": _fmt(total),
        "change_str": _fmt(abs(change)),
        "change_pct_str": f"{abs(change_pct):.2f}".replace(".", ","),
        "is_up": change >= 0,
    }


@router.get("/home")
def home_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)
    investment_summary = _get_investment_summary(db, user.id, checking_account)
    credit_card = CreditCardRepository.get_by_user_id(db, user.id)

    flash = request.query_params.get("flash")

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "request": request,
            "active_page": "home",
            "dashboard_label": "Painel financeiro",
            "user": user,
            "checking_account": checking_account,
            "savings_account": savings_account,
            "investment_summary": investment_summary,
            "credit_card": credit_card,
            "flash": flash,
        },
    )


@router.post("/home/abrir-poupanca")
def open_savings_account(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    existing = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)
    if not existing:
        AccountRepository.create(db, user_id=user.id, type=AccountType.SAVINGS)
        db.commit()

    return RedirectResponse("/home", status_code=303)