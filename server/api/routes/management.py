from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from server.api.routes.auth import get_current_manager_user
from server.db.connection import get_db
from server.models.account import Account
from server.models.user import User, UserType
from server.repositories.account_repository import AccountRepository
from server.repositories.user_repository import UserRepository

router = APIRouter(prefix="/management", tags=["management"])


class UpdateUserNamePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _user_type_value(user: User) -> str:
    t = user.type
    return t.value if hasattr(t, "value") else str(t)


def _account_type_value(account: Account) -> str:
    t = account.type
    return t.value if hasattr(t, "value") else str(t)


@router.get("/overview")
def management_overview(
    _: User = Depends(get_current_manager_user),
    db=Depends(get_db),
) -> dict[str, int]:
    return {
        "total_users": UserRepository.count_all(db),
        "total_managers": UserRepository.count_by_type(db, UserType.MANAGER),
        "total_accounts": AccountRepository.count_all(db),
    }


@router.get("/users-accounts")
def list_users_and_accounts(
    _: User = Depends(get_current_manager_user),
    db=Depends(get_db),
) -> dict[str, object]:
    users = UserRepository.list_all(db)
    user_ids = [user.id for user in users]
    accounts_by_user = AccountRepository.get_grouped_by_user_ids(db, user_ids)

    data = []
    for user in users:
        accounts = accounts_by_user.get(user.id, [])
        data.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "cpf": user.cpf,
                "type": _user_type_value(user),
                "accounts": [
                    {
                        "id": account.id,
                        "account_number": account.account_number,
                        "agency": account.agency,
                        "type": _account_type_value(account),
                        "balance": str(account.balance),
                    }
                    for account in accounts
                ],
            }
        )

    return {"users": data}


@router.patch("/users/{user_id}/name")
def update_user_name(
    user_id: int,
    payload: UpdateUserNamePayload,
    _: User = Depends(get_current_manager_user),
    db=Depends(get_db),
) -> dict[str, object]:
    name = payload.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome nao pode ser vazio.",
        )

    user = UserRepository.update_name(db, user_id=user_id, name=name)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    db.commit()
    return {
        "id": user.id,
        "name": user.name,
        "message": "Nome do usuario atualizado com sucesso.",
    }
