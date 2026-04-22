from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.api.routes.auth import get_current_manager_user
from server.db.session import get_db
from server.models.orm_models import TipoUsuario, Usuario
from server.repositories.conta_repository import ContaRepository
from server.repositories.usuario_repository import UsuarioRepository

router = APIRouter(prefix="/management", tags=["management"])


class UpdateUserNamePayload(BaseModel):
    nome: str = Field(min_length=1, max_length=100)


def _tipo_usuario_value(user: Usuario) -> str:
    tipo = user.tipo_usuario
    return tipo.value if hasattr(tipo, "value") else str(tipo)


def _tipo_conta_value(conta) -> str:
    tipo = conta.tipo_conta
    return tipo.value if hasattr(tipo, "value") else str(tipo)


@router.get("/overview")
def management_overview(
    _: Usuario = Depends(get_current_manager_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {
        "total_usuarios": UsuarioRepository.count_all(db),
        "total_gerentes": UsuarioRepository.count_by_tipo(db, TipoUsuario.MANAGER),
        "total_contas": ContaRepository.count_all(db),
    }


@router.get("/users-accounts")
def list_users_and_accounts(
    _: Usuario = Depends(get_current_manager_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    usuarios = UsuarioRepository.list_all(db)
    usuario_ids = [usuario.id for usuario in usuarios]
    contas_por_usuario = ContaRepository.get_grouped_by_usuario_ids(db, usuario_ids)

    data = []
    for usuario in usuarios:
        contas = contas_por_usuario.get(usuario.id, [])
        data.append(
            {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "cpf": usuario.cpf,
                "tipo_usuario": _tipo_usuario_value(usuario),
                "contas": [
                    {
                        "id": conta.id,
                        "numero_conta": conta.numero_conta,
                        "agencia": conta.agencia,
                        "tipo_conta": _tipo_conta_value(conta),
                        "saldo": str(conta.saldo),
                    }
                    for conta in contas
                ],
            }
        )

    return {"usuarios": data}


@router.patch("/users/{usuario_id}/name")
def update_user_name(
    usuario_id: int,
    payload: UpdateUserNamePayload,
    _: Usuario = Depends(get_current_manager_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    nome = payload.nome.strip()
    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome nao pode ser vazio.",
        )

    usuario = UsuarioRepository.update_nome(db, usuario_id=usuario_id, nome=nome)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    db.commit()
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "message": "Nome do usuario atualizado com sucesso.",
    }
