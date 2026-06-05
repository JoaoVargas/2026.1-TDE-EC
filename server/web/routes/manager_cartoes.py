from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.credit_card_repository import CreditCardRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])

_FEEDBACK = {
    "cartao_criado": ("Cartão criado com sucesso.", False),
    "cartao_cancelado": ("Cartão cancelado com sucesso.", False),
    "limite_atualizado": ("Limite atualizado com sucesso.", False),
    "fatura_pendente": ("Não é possível cancelar um cartão com fatura em aberto.", True),
    "cartao_nao_encontrado": ("Cartão não encontrado.", True),
    "usuario_nao_encontrado": ("Usuário não encontrado.", True),
    "limite_invalido": ("Limite inválido. Informe um valor positivo.", True),
    "limite_invalido_gerente": ("Limite inválido. Use incrementos de R$1.000 entre R$1.000 e R$100.000.", True),
    "limite_abaixo_fatura": ("Limite não pode ser menor que a fatura atual.", True),
    "cartao_ja_existe": ("Este usuário já possui um cartão de crédito.", True),
}


@router.get("/manager/cartoes")
def manager_cartoes_page(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    manager = result

    all_cards = CreditCardRepository.list_all(db)
    all_users = UserRepository.list_all(db)
    users_by_id = {u.id: u for u in all_users}

    cards_data = []
    for card in all_cards:
        u = users_by_id.get(card.user_id)
        cards_data.append({
            "id": card.id,
            "user_id": card.user_id,
            "user_name": u.name if u else "—",
            "user_email": u.email if u else "—",
            "masked_number": card.masked_number,
            "limit_amount": float(card.limit_amount),
            "used_amount": float(card.used_amount),
            "available_amount": float(card.available_amount),
            "limit_cents": int(card.limit_amount * 100),
            "used_cents": int(card.used_amount * 100),
            "status": card.status.value,
            "can_cancel": card.used_amount == 0,
        })

    card_user_ids = {c["user_id"] for c in cards_data}
    clients_without_card = [
        {"id": u.id, "name": u.name, "email": u.email}
        for u in all_users
        if (u.type.value if hasattr(u.type, "value") else str(u.type)) == "client"
        and u.id not in card_user_ids
    ]

    feedback_key = request.query_params.get("feedback")
    feedback_entry = _FEEDBACK.get(feedback_key)

    return templates.TemplateResponse(
        request=request,
        name="manager_cartoes.html",
        context={
            "request": request,
            "active_page": "manager_cartoes",
            "dashboard_label": "Gestão de cartões",
            "sidebar_template": "components/manager_sidebar.html",
            "user": manager,
            "cards": cards_data,
            "clients_without_card": clients_without_card,
            "feedback": feedback_entry[0] if feedback_entry else None,
            "feedback_is_error": feedback_entry[1] if feedback_entry else False,
        },
    )


@router.post("/manager/cartoes/criar")
async def manager_criar_cartao(
    request: Request,
    user_id: int = Form(...),
    limit_cents: int = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    if limit_cents <= 0:
        return RedirectResponse("/manager/cartoes?feedback=limite_invalido", status_code=302)

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        return RedirectResponse("/manager/cartoes?feedback=usuario_nao_encontrado", status_code=302)

    if CreditCardRepository.get_by_user_id(db, user_id):
        return RedirectResponse("/manager/cartoes?feedback=cartao_ja_existe", status_code=302)

    limit = Decimal(limit_cents) / 100
    CreditCardRepository.create(db, user_id=user_id, card_name=user.name.upper(), limit_amount=limit)
    db.commit()
    return RedirectResponse("/manager/cartoes?feedback=cartao_criado", status_code=302)


@router.post("/manager/cartoes/{card_id}/cancelar")
async def manager_cancelar_cartao(
    card_id: int,
    request: Request,
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    card = CreditCardRepository.get_by_id(db, card_id)
    if not card:
        return RedirectResponse("/manager/cartoes?feedback=cartao_nao_encontrado", status_code=302)
    if card.used_amount > 0:
        return RedirectResponse("/manager/cartoes?feedback=fatura_pendente", status_code=302)

    CreditCardRepository.delete(db, card_id=card_id)
    db.commit()
    return RedirectResponse("/manager/cartoes?feedback=cartao_cancelado", status_code=302)


@router.post("/manager/cartoes/{card_id}/limite")
async def manager_ajustar_limite(
    card_id: int,
    request: Request,
    new_limit_cents: int = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    _MIN = 100_000   # R$1.000 in cents
    _MAX = 10_000_000  # R$100.000 in cents
    _STEP = 100_000  # R$1.000 in cents

    if new_limit_cents < _MIN or new_limit_cents > _MAX or new_limit_cents % _STEP != 0:
        return RedirectResponse("/manager/cartoes?feedback=limite_invalido_gerente", status_code=302)

    card = CreditCardRepository.get_by_id(db, card_id)
    if not card:
        return RedirectResponse("/manager/cartoes?feedback=cartao_nao_encontrado", status_code=302)

    new_limit = Decimal(new_limit_cents) / 100
    if new_limit < card.used_amount:
        return RedirectResponse("/manager/cartoes?feedback=limite_abaixo_fatura", status_code=302)

    CreditCardRepository.update_limit(db, card_id=card_id, new_limit=new_limit)
    db.commit()
    return RedirectResponse("/manager/cartoes?feedback=limite_atualizado", status_code=302)
