from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.models.transaction import TransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])

_VALID_MODES = ("depositar", "sacar", "transferir")

_ERROR_MAPS = {
    "depositar": {
        "valor_invalido": "Valor de depósito inválido.",
        "sem_conta": "Conta corrente não encontrada.",
    },
    "sacar": {
        "saldo_insuficiente": "Saldo insuficiente para este saque.",
        "valor_invalido": "Valor de saque inválido.",
        "sem_conta": "Conta corrente não encontrada.",
    },
    "transferir": {
        "saldo_insuficiente": "Saldo insuficiente para esta transferência.",
        "valor_invalido": "Valor de transferência inválido.",
        "destinatario_invalido": "Destinatário não encontrado.",
        "sem_conta": "Nenhuma conta encontrada para o usuário.",
    },
}

_ACTIVE_PAGE = {"depositar": "deposito", "sacar": "saque", "transferir": "transacao"}
_DASHBOARD_LABEL = {"depositar": "Depositar", "sacar": "Sacar", "transferir": "Transferir"}


def _build_other_accounts(db, exclude_user_id: int) -> list[dict]:
    result = []
    for u in UserRepository.list_all(db):
        if u.id == exclude_user_id:
            continue
        acc = AccountRepository.get_by_user_and_type(db, u.id, AccountType.CHECKING)
        if acc:
            result.append({"id": acc.id, "account_number": acc.account_number, "owner_name": u.name})
    return result


@router.get("/operacao")
def operacao_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    modo = request.query_params.get("modo", "depositar")
    if modo not in _VALID_MODES:
        modo = "depositar"

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)
    other_accounts = _build_other_accounts(db, user.id) if modo == "transferir" else []

    error_key = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="operacao.html",
        context={
            "request": request,
            "active_page": _ACTIVE_PAGE[modo],
            "dashboard_label": _DASHBOARD_LABEL[modo],
            "user": user,
            "modo": modo,
            "checking_account": checking_account,
            "savings_account": savings_account,
            "other_accounts": other_accounts,
            "error": _ERROR_MAPS[modo].get(error_key) if error_key else None,
        },
    )


@router.post("/operacao")
async def operacao_submit(
    request: Request,
    modo: str = Form(...),
    amount_cents: int = Form(...),
    to_account_id: Optional[int] = Form(None),
    from_account_type: str = Form("corrente"),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    if modo not in _VALID_MODES:
        return RedirectResponse("/operacao", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse(f"/operacao?modo={modo}&error=valor_invalido", status_code=302)

    if modo == "depositar":
        account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
        if not account:
            return RedirectResponse("/operacao?modo=depositar&error=sem_conta", status_code=302)

        cursor = db.cursor()
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account.id))
        cursor.close()
        TransactionRepository.create(db, type=TransactionType.DEPOSIT, from_account_id=None, to_account_id=account.id, amount=amount, description=None)
        db.commit()
        return RedirectResponse("/home?flash=deposito_realizado", status_code=302)

    if modo == "sacar":
        account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
        if not account:
            return RedirectResponse("/operacao?modo=sacar&error=sem_conta", status_code=302)
        if account.balance < amount:
            return RedirectResponse("/operacao?modo=sacar&error=saldo_insuficiente", status_code=302)

        cursor = db.cursor()
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account.id))
        cursor.close()
        TransactionRepository.create(db, type=TransactionType.WITHDRAWAL, from_account_id=account.id, to_account_id=None, amount=amount, description=None)
        db.commit()
        return RedirectResponse("/home?flash=saque_realizado", status_code=302)

    # modo == "transferir"
    tipo = AccountType.SAVINGS if from_account_type == "poupanca" else AccountType.CHECKING
    from_account = AccountRepository.get_by_user_and_type(db, user.id, tipo)
    if not from_account:
        return RedirectResponse("/operacao?modo=transferir&error=sem_conta", status_code=302)

    to_account = AccountRepository.get_by_id(db, to_account_id) if to_account_id else None
    if not to_account:
        return RedirectResponse("/operacao?modo=transferir&error=destinatario_invalido", status_code=302)

    own_transfer = to_account.user_id == user.id and to_account.id != from_account.id
    external_transfer = to_account.user_id != user.id and to_account.type == AccountType.CHECKING
    if not own_transfer and not external_transfer:
        return RedirectResponse("/operacao?modo=transferir&error=destinatario_invalido", status_code=302)

    if from_account.balance < amount:
        return RedirectResponse("/operacao?modo=transferir&error=saldo_insuficiente", status_code=302)

    cursor = db.cursor()
    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, from_account.id))
    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to_account.id))
    cursor.close()
    TransactionRepository.create(db, type=TransactionType.TRANSACTION, from_account_id=from_account.id, to_account_id=to_account.id, amount=amount, description=None)
    db.commit()
    return RedirectResponse("/home?flash=transferencia_realizada", status_code=302)
