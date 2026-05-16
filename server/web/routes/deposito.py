from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from server.models.account import AccountType
from server.db.connection import get_db
from server.models.transaction import TransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.transaction_repository import TransactionRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])

_ERROR_MAP = {
    "valor_invalido": "Valor de depósito inválido.",
    "sem_conta": "Nenhuma conta encontrada para o usuário.",
}


@router.get("/depositar")
def deposito_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)
    error_key = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="deposito.html",
        context={
            "request": request,
            "active_page": "deposito",
            "dashboard_label": "Depositar",
            "user": user,
            "checking_account": checking_account,
            "savings_account": savings_account,
            "error": _ERROR_MAP.get(error_key),
        },
    )


@router.post("/depositar")
async def deposito_submit(
    request: Request,
    amount_cents: int = Form(...),
    account_type: str = Form("corrente"),  # novo
    db=Depends(get_db),
):
    print(f"[DEBUG] account_type recebido={account_type} | amount_cents={amount_cents}")
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    # Busca a conta correta pelo tipo
    tipo = AccountType.SAVINGS if account_type == "poupanca" else AccountType.CHECKING
    account = AccountRepository.get_by_user_and_type(db, user.id, tipo)

    if not account:
        return RedirectResponse("/depositar?error=sem_conta", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse("/depositar?error=valor_invalido", status_code=302)

    cursor = db.cursor()
    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE id = %s",
        (amount, account.id),
    )
    cursor.close()

    TransactionRepository.create(
        db,
        type=TransactionType.DEPOSIT,
        from_account_id=None,
        to_account_id=account.id,
        amount=amount,
        description=None,
    )
    db.commit()

    return RedirectResponse("/home?flash=deposito_realizado", status_code=302)
