from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.account_repository import AccountRepository
from server.repositories.address_repository import AddressRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])


def _serialize_users(users, accounts_by_user: dict, addresses_by_id: dict) -> list[dict]:
    result = []
    for u in users:
        accounts = accounts_by_user.get(u.id, [])
        addr = addresses_by_id.get(u.address_id)
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "cpf": u.cpf,
            "address_id": u.address_id,
            "type": u.type.value if hasattr(u.type, "value") else str(u.type),
            "address": {
                "cep": addr.cep if addr else "",
                "street": addr.street if addr else "",
                "number": addr.number if addr else "",
                "neighborhood": addr.neighborhood if addr else "",
                "city": addr.city if addr else "",
                "state": addr.state if addr else "",
            },
            "accounts": [
                {
                    "id": acc.id,
                    "account_number": acc.account_number,
                    "agency": acc.agency,
                    "type": acc.type.value if hasattr(acc.type, "value") else str(acc.type),
                    "balance": float(acc.balance),
                }
                for acc in accounts
            ],
        })
    return result


@router.get("/manager/accounts")
def manager_accounts_page(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result
    manager = result

    users = UserRepository.list_all(db)
    accounts_by_user = AccountRepository.get_grouped_by_user_ids(db, [u.id for u in users])

    address_ids = [u.address_id for u in users if u.address_id]
    addresses_by_id = {aid: AddressRepository.get_by_id(db, aid) for aid in address_ids}

    users_data = _serialize_users(users, accounts_by_user, addresses_by_id)

    feedback_map = {
        "perfil_atualizado": "Nome e email atualizados com sucesso.",
        "perfil_invalido": "Nome ou email inválido.",
        "nome_atualizado": "Nome atualizado com sucesso.",
        "nome_invalido": "Nome inválido.",
        "cpf_atualizado": "CPF atualizado com sucesso.",
        "cpf_invalido": "CPF inválido. Informe 11 dígitos.",
        "endereco_atualizado": "Endereço atualizado com sucesso.",
        "endereco_invalido": "Endereço inválido. Verifique os campos.",
        "usuario_nao_encontrado": "Usuário não encontrado.",
    }
    feedback_key = request.query_params.get("feedback")

    return templates.TemplateResponse(
        request=request,
        name="manager_accounts.html",
        context={
            "request": request,
            "active_page": "manager_accounts",
            "dashboard_label": "Gestão de usuários e contas",
            "sidebar_template": "components/manager_sidebar.html",
            "user": manager,
            "users": users_data,
            "feedback": feedback_map.get(feedback_key),
        },
    )


@router.post("/manager/accounts/{user_id}/profile")
async def manager_update_profile(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    name = name.strip()
    email = email.strip()
    if not name or not email or "@" not in email:
        return RedirectResponse("/manager/accounts?feedback=perfil_invalido", status_code=302)

    updated = UserRepository.update_profile(db, user_id=user_id, name=name, email=email)
    if not updated:
        return RedirectResponse("/manager/accounts?feedback=usuario_nao_encontrado", status_code=302)

    db.commit()
    return RedirectResponse("/manager/accounts?feedback=perfil_atualizado", status_code=302)


@router.post("/manager/accounts/{user_id}/rename")
async def manager_rename_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    name = name.strip()
    if not name:
        return RedirectResponse("/manager/accounts?feedback=nome_invalido", status_code=302)

    updated = UserRepository.update_name(db, user_id=user_id, name=name)
    if not updated:
        return RedirectResponse("/manager/accounts?feedback=usuario_nao_encontrado", status_code=302)

    db.commit()
    return RedirectResponse("/manager/accounts?feedback=nome_atualizado", status_code=302)


@router.post("/manager/accounts/{user_id}/cpf")
async def manager_update_cpf(
    user_id: int,
    request: Request,
    cpf: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    cpf_clean = "".join(c for c in cpf if c.isdigit())
    if len(cpf_clean) != 11:
        return RedirectResponse("/manager/accounts?feedback=cpf_invalido", status_code=302)

    updated = UserRepository.update_cpf(db, user_id=user_id, cpf=cpf_clean)
    if not updated:
        return RedirectResponse("/manager/accounts?feedback=usuario_nao_encontrado", status_code=302)

    db.commit()
    return RedirectResponse("/manager/accounts?feedback=cpf_atualizado", status_code=302)


@router.post("/manager/accounts/{user_id}/endereco")
async def manager_update_endereco(
    user_id: int,
    request: Request,
    cep: str = Form(...),
    street: str = Form(...),
    number: str = Form(...),
    neighborhood: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    db=Depends(get_db),
):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        return RedirectResponse("/manager/accounts?feedback=usuario_nao_encontrado", status_code=302)

    cep_clean = "".join(c for c in cep if c.isdigit())
    if len(cep_clean) != 8 or not street.strip() or not state.strip() or not city.strip():
        return RedirectResponse("/manager/accounts?feedback=endereco_invalido", status_code=302)

    AddressRepository.update(
        db,
        address_id=user.address_id,
        cep=cep_clean,
        street=street.strip(),
        state=state.strip().upper(),
        city=city.strip(),
        neighborhood=neighborhood.strip(),
        number=number.strip(),
    )
    db.commit()
    return RedirectResponse("/manager/accounts?feedback=endereco_atualizado", status_code=302)
