from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.account_repository import AccountRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_manager, templates

router = APIRouter(tags=["pages"])


def _serialize_users(users, accounts_by_user: dict) -> list[dict]:
    result = []
    for u in users:
        accounts = accounts_by_user.get(u.id, [])
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "cpf": u.cpf,
            "type": u.type.value if hasattr(u.type, "value") else str(u.type),
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
    users_data = _serialize_users(users, accounts_by_user)

    feedback_map = {
        "nome_atualizado": "Nome atualizado com sucesso.",
        "nome_invalido": "Nome inválido.",
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
