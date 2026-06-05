from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.models.account import AccountType
from server.models.credit_card import CreditCardTransactionType
from server.repositories.account_repository import AccountRepository
from server.repositories.credit_card_repository import CreditCardRepository
from server.repositories.transaction_repository import TransactionRepository
from server.models.transaction import TransactionType
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])

_MAX_LIMIT = Decimal("5000.00")
_MIN_LIMIT = Decimal("100.00")
_LIMIT_STEP = Decimal("100.00")

_ERROR_MESSAGES = {
    "saldo_insuficiente": "Saldo insuficiente na conta corrente para este pagamento.",
    "fatura_zerada": "Sua fatura já está zerada.",
    "limite_insuficiente": "Limite insuficiente para esta compra.",
    "valor_invalido": "Valor inválido.",
    "sem_cartao": "Você ainda não possui cartão de crédito.",
    "sem_conta": "Conta corrente não encontrada.",
    "cartao_ja_existe": "Você já possui um cartão de crédito.",
    "limite_invalido": "Limite inválido. Escolha entre R$100 e R$5.000.",
    "limite_abaixo_fatura": "O novo limite não pode ser menor que sua fatura atual.",
}

_FLASH_MESSAGES = {
    "pagamento_realizado": "Pagamento da fatura realizado com sucesso!",
    "compra_realizada": "Compra simulada com sucesso!",
    "cartao_solicitado": "Cartão solicitado com sucesso!",
    "limite_atualizado": "Limite atualizado com sucesso!",
}


def _fmt_brl(value: Decimal) -> str:
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


@router.get("/cartao")
def cartao_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    card = CreditCardRepository.get_by_user_id(db, user.id)
    transactions = []
    total_paid = Decimal("0")
    total_spent = Decimal("0")

    if card:
        raw_txs = CreditCardRepository.get_transactions(db, card.id)
        for tx in raw_txs:
            is_purchase = tx.type == CreditCardTransactionType.PURCHASE
            date_str = tx.created_at.strftime("%d/%m/%Y · %H:%M") if tx.created_at else "-"
            month = str(tx.created_at.month) if tx.created_at else ""
            if is_purchase:
                total_spent += tx.amount
            else:
                total_paid += tx.amount
            transactions.append({
                "kind": "out" if is_purchase else "in",
                "month": month,
                "title": tx.description or ("Compra" if is_purchase else "Pagamento da fatura"),
                "date_str": date_str,
                "amount_str": _fmt_brl(tx.amount),
            })

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    flash_key = request.query_params.get("flash")
    error_key = request.query_params.get("error")

    return templates.TemplateResponse(
        request=request,
        name="cartao.html",
        context={
            "request": request,
            "active_page": "cartao",
            "dashboard_label": "Cartão de Crédito",
            "user": user,
            "card": card,
            "transactions": transactions,
            "total_paid_str": _fmt_brl(total_paid),
            "total_spent_str": _fmt_brl(total_spent),
            "checking_account": checking_account,
            "max_limit_cents": int(_MAX_LIMIT * 100),
            "min_limit_cents": int(_MIN_LIMIT * 100),
            "flash": _FLASH_MESSAGES.get(flash_key) if flash_key else None,
            "error": _ERROR_MESSAGES.get(error_key) if error_key else None,
        },
    )


@router.post("/cartao/solicitar")
async def cartao_solicitar(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    existing = CreditCardRepository.get_by_user_id(db, user.id)
    if existing:
        return RedirectResponse("/cartao?error=cartao_ja_existe", status_code=302)

    CreditCardRepository.create(db, user_id=user.id, card_name=user.name.upper())
    db.commit()
    return RedirectResponse("/cartao?flash=cartao_solicitado", status_code=302)


@router.post("/cartao/pagar")
async def cartao_pagar(
    request: Request,
    amount_cents: int = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    card = CreditCardRepository.get_by_user_id(db, user.id)
    if not card:
        return RedirectResponse("/cartao?error=sem_cartao", status_code=302)
    if card.used_amount <= 0:
        return RedirectResponse("/cartao?error=fatura_zerada", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse("/cartao?error=valor_invalido", status_code=302)

    checking = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)
    if not checking:
        return RedirectResponse("/cartao?error=sem_conta", status_code=302)

    pay_amount = min(amount, card.used_amount)
    if checking.balance < pay_amount:
        return RedirectResponse("/cartao?error=saldo_insuficiente", status_code=302)

    cursor = db.cursor()
    cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (pay_amount, checking.id))
    cursor.close()

    CreditCardRepository.apply_payment(db, card_id=card.id, amount=pay_amount)
    CreditCardRepository.create_transaction(
        db,
        credit_card_id=card.id,
        type=CreditCardTransactionType.PAYMENT,
        amount=pay_amount,
        description="Pagamento da fatura",
    )
    TransactionRepository.create(
        db,
        type=TransactionType.EXPENSE,
        from_account_id=checking.id,
        to_account_id=None,
        amount=pay_amount,
        description="Pagamento fatura cartão de crédito",
    )
    db.commit()
    return RedirectResponse("/cartao?flash=pagamento_realizado", status_code=302)


@router.post("/cartao/usar")
async def cartao_usar(
    request: Request,
    amount_cents: int = Form(...),
    description: Optional[str] = Form("Compra"),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    card = CreditCardRepository.get_by_user_id(db, user.id)
    if not card:
        return RedirectResponse("/cartao?error=sem_cartao", status_code=302)

    amount = Decimal(amount_cents) / 100
    if amount <= 0:
        return RedirectResponse("/cartao?error=valor_invalido", status_code=302)

    if card.available_amount < amount:
        return RedirectResponse("/cartao?error=limite_insuficiente", status_code=302)

    desc = (description or "Compra").strip() or "Compra"
    CreditCardRepository.apply_purchase(db, card_id=card.id, amount=amount)
    CreditCardRepository.create_transaction(
        db,
        credit_card_id=card.id,
        type=CreditCardTransactionType.PURCHASE,
        amount=amount,
        description=desc,
    )
    db.commit()
    return RedirectResponse("/cartao?flash=compra_realizada", status_code=302)


@router.post("/cartao/limite")
async def cartao_limite(
    request: Request,
    new_limit_cents: int = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    card = CreditCardRepository.get_by_user_id(db, user.id)
    if not card:
        return RedirectResponse("/cartao?error=sem_cartao", status_code=302)

    new_limit = Decimal(new_limit_cents) / 100
    if new_limit < _MIN_LIMIT or new_limit > _MAX_LIMIT:
        return RedirectResponse("/cartao?error=limite_invalido", status_code=302)
    if new_limit < card.used_amount:
        return RedirectResponse("/cartao?error=limite_abaixo_fatura", status_code=302)

    CreditCardRepository.update_limit(db, card_id=card.id, new_limit=new_limit)
    db.commit()
    return RedirectResponse("/cartao?flash=limite_atualizado", status_code=302)
