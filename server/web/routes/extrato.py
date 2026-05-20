from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.models.transaction import TransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.transaction_repository import TransactionRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


def _fmt_brl(value: Decimal) -> str:
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _enrich_transaction(tx, account_id: int) -> dict:
    date_str = tx.created_at.strftime("%d/%m/%Y · %H:%M") if tx.created_at else "-"
    month = str(tx.created_at.month) if tx.created_at else "0"

    if tx.type == TransactionType.DEPOSIT:
        kind = "in"
        label = tx.description or "Depósito"
    elif tx.type == TransactionType.WITHDRAWAL:
        kind = "out"
        label = tx.description or "Saque"
    else:
        is_incoming = tx.to_account_id == account_id
        kind = "in" if is_incoming else "out"
        label = tx.description or ("Transferência recebida" if is_incoming else "Transferência enviada")

    prefix = "+" if kind == "in" else "-"
    amount_str = f"{prefix} {_fmt_brl(tx.amount)}"

    return {
        "kind": kind,
        "month": month,
        "title": label,
        "date_str": date_str,
        "amount_str": amount_str,
        "raw_amount": tx.amount,
    }


@router.get("/extrato")
def extrato_page(request: Request, account: str = "corrente", db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)

    selected_type = "poupanca" if (account == "poupanca" and savings_account) else "corrente"
    active_account = savings_account if selected_type == "poupanca" else checking_account

    transactions = []
    total_in = Decimal("0")
    total_out = Decimal("0")

    if active_account:
        for tx in TransactionRepository.get_by_account_id(db, active_account.id):
            enriched = _enrich_transaction(tx, active_account.id)
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
            "account": active_account,
            "savings_account": savings_account,
            "selected_account_type": selected_type,
            "transactions": transactions,
            "balance_str": _fmt_brl(active_account.balance) if active_account else "R$ 0,00",
            "total_in_str": _fmt_brl(total_in),
            "total_out_str": _fmt_brl(total_out),
        },
    )
