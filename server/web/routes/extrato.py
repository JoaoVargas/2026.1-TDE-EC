from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.account_repository import AccountRepository
from server.repositories.transaction_repository import TransactionRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


def _fmt_brl(value: Decimal) -> str:
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _enrich_transaction(tx, account_id: int) -> dict:
    is_incoming = tx.to_account_id == account_id
    kind = "in" if is_incoming else "out"
    prefix = "+" if is_incoming else "-"
    amount_str = f"{prefix} {_fmt_brl(tx.amount)}"
    date_str = tx.created_at.strftime("%d/%m/%Y · %H:%M") if tx.created_at else "-"
    month = str(tx.created_at.month) if tx.created_at else "0"
    label = tx.description or ("Transferência recebida" if is_incoming else "Transferência enviada")
    return {
        "kind": kind,
        "month": month,
        "title": label,
        "date_str": date_str,
        "amount_str": amount_str,
        "raw_amount": tx.amount,
    }


@router.get("/extrato")
def extrato_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    accounts = AccountRepository.get_by_user_id(db, user.id)
    account = accounts[0] if accounts else None

    transactions = []
    total_in = Decimal("0")
    total_out = Decimal("0")

    if account:
        for tx in TransactionRepository.get_by_account_id(db, account.id):
            enriched = _enrich_transaction(tx, account.id)
            transactions.append(enriched)
            if enriched["kind"] == "in":
                total_in += enriched["raw_amount"]
            else:
                total_out += enriched["raw_amount"]

    return templates.TemplateResponse(
        request=request,
        name="extrato.html",
        context={
            "request": request,
            "active_page": "extrato",
            "dashboard_label": "Extrato",
            "user": user,
            "account": account,
            "transactions": transactions,
            "balance_str": _fmt_brl(account.balance) if account else "R$ 0,00",
            "total_in_str": _fmt_brl(total_in),
            "total_out_str": _fmt_brl(total_out),
        },
    )
