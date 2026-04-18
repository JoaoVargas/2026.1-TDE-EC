from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from server.core.settings import get_settings
from server.db.session import get_db
from server.models.orm_models import Usuario

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)


class EnderecoCadastro(BaseModel):
    cep: str = Field(min_length=8, max_length=9)
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str = Field(min_length=2, max_length=2)


class CadastroPayload(BaseModel):
    nome: str
    email: str
    cpf: str
    nascimento: str
    senha: str = Field(min_length=8)
    endereco: EnderecoCadastro


class LoginPayload(BaseModel):
    cpf: str
    senha: str


def _normalize_cpf(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nao autenticado.")

    token = credentials.credentials
    try:
        payload = _decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.")

    user = db.get(Usuario, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado.")

    return user


@router.get("/verificar")
def verificar_disponibilidade(
    cpf: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not cpf and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe cpf ou email para verificacao.",
        )

    filtros = []
    if cpf:
        filtros.append(Usuario.cpf == _normalize_cpf(cpf))
    if email:
        filtros.append(Usuario.email == email.strip().lower())

    query = select(Usuario.id).where(or_(*filtros))
    existe = db.execute(query).first() is not None
    return {"disponivel": not existe}


@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(payload: CadastroPayload, db: Session = Depends(get_db)) -> dict[str, str]:
    cpf = _normalize_cpf(payload.cpf)
    email = payload.email.strip().lower()

    if len(cpf) != 11:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CPF invalido.")

    duplicate = db.execute(
        select(Usuario.id).where(or_(Usuario.cpf == cpf, Usuario.email == email))
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF ou e-mail ja cadastrado.")

    try:
        data_nascimento = datetime.strptime(payload.nascimento, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data de nascimento invalida.",
        )

    novo_usuario = Usuario(
        nome=payload.nome.strip(),
        email=email,
        senha=_hash_password(payload.senha),
        data_nascimento=data_nascimento,
        cpf=cpf,
        cep="".join(char for char in payload.endereco.cep if char.isdigit()),
        logradouro=payload.endereco.logradouro.strip(),
        numero=payload.endereco.numero.strip(),
        bairro=payload.endereco.bairro.strip(),
        cidade=payload.endereco.cidade.strip(),
        estado=payload.endereco.estado.strip().upper(),
    )

    db.add(novo_usuario)
    db.commit()

    return {"message": "Cadastro realizado com sucesso."}


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    login_value = payload.cpf.strip()
    lookup = Usuario.email == login_value.lower() if "@" in login_value else Usuario.cpf == _normalize_cpf(login_value)
    user = db.execute(select(Usuario).where(lookup)).scalar_one_or_none()

    if not user or not _verify_password(payload.senha, user.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF/e-mail ou senha incorretos.",
        )

    token = _create_access_token(str(user.id))
    return {
        "token": token,
        "usuario": {
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "cpf": user.cpf,
        },
    }


@router.get("/me")
def me(current_user: Usuario = Depends(get_current_user)) -> dict[str, object]:
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "cpf": current_user.cpf,
    }