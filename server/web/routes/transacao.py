from decimal import Decimal

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


def _build_other_accounts(db, exclude_user_id: int) -> list[dict]:
    users = UserRepository.list_all(db)
    result = []
    for u in users:
        if u.id == exclude_user_id:
            continue
        for acc in AccountRepository.get_by_user_id(db, u.id):
            result.append({
                "id": acc.id,
                "account_number": acc.account_number,
                "owner_name": u.name,
            })
    return result


@router.get("/transferir")
def transacao_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    savings_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.SAVINGS)
    other_accounts = _build_other_accounts(db, user.id)

    error_map = {
        "saldo_insuficiente": "Saldo insuficiente para esta transferência.",
        "valor_invalido": "Valor de transferência inválido.",
        "destinatario_invalido": "Destinatário não encontrado.",
        "sem_conta": "Nenhuma conta encontrada para o usuário.",
    }
    error_key = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="transacao.html",
        context={
            "request": request,
            "active_page": "transacao",
            "dashboard_label": "Transferir",
            "user": user,
            "checking_account": checking_account,
            "savings_account": savings_account,
            "other_accounts": other_accounts,
            "error": error_map.get(error_key),
        },
    )


@router.post("/transacao")
async def transacao_submit(
    request: Request,
    amount_cents: int = Form(...),
    to_account_id: int = Form(...),
    from_account_type: str = Form("corrente"),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    tipo = AccountType.SAVINGS if from_account_type == "poupanca" else AccountType.CHECKING
    from_account = AccountRepository.get_by_user_and_type(db, user.id, tipo)

    if not from_account:
        return RedirectResponse("/transferir?error=sem_conta", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse("/transferir?error=valor_invalido", status_code=302)

    to_account = AccountRepository.get_by_id(db, to_account_id)
    if not to_account:
        return RedirectResponse("/transferir?error=destinatario_invalido", status_code=302)

    if from_account.balance < amount:
        return RedirectResponse("/transferir?error=saldo_insuficiente", status_code=302)

    cursor = db.cursor()
    cursor.execute(
        "UPDATE accounts SET balance = balance - %s WHERE id = %s",
        (amount, from_account.id),
    )
    cursor.execute(
        "UPDATE accounts SET balance = balance + %s WHERE id = %s",
        (amount, to_account.id),
    )
    cursor.close()

    TransactionRepository.create(
        db,
        type=TransactionType.TRANSACTION,
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=amount,
        description=None,
    )
    db.commit()

    return RedirectResponse("/home?flash=transferencia_realizada", status_code=302)


@router.post("/transferir/{transaction_id}/descricao")
def transacao_update_descricao(
    transaction_id: int,
    request: Request,
    descricao: str = Form(default=""),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result

    TransactionRepository.update_description(
        db,
        transaction_id=transaction_id,
        description=descricao.strip() or None,
    )
    db.commit()
    return RedirectResponse("/extrato", status_code=302)


@router.post("/transferir/{transaction_id}/deletar")
def transacao_delete(
    transaction_id: int,
    request: Request,
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result

    TransactionRepository.delete(db, transaction_id=transaction_id)
    db.commit()
    return RedirectResponse("/extrato", status_code=302)