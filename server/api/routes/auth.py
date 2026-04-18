from datetime import date, datetime, timedelta, timezone
import re

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.core.settings import get_settings
from server.db.session import get_db
from server.models.orm_models import Usuario

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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
    nascimento: date
    senha: str = Field(min_length=8)
    endereco: EnderecoCadastro


class LoginPayload(BaseModel):
    cpf: str
    senha: str


def _normalize_cpf(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _normalize_cep(value: str) -> str:
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


def _decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nao autenticado.")

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.")

    token = credentials.credentials
    try:
        payload = _decode_access_token(token)
        subject = payload.get("sub")
        user_id = int(str(subject))
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
        filtros.append(Usuario.email == _normalize_email(email))

    query = select(Usuario.id).where(or_(*filtros))
    existe = db.execute(query).first() is not None
    return {"disponivel": not existe}


@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(payload: CadastroPayload, db: Session = Depends(get_db)) -> dict[str, str]:
    cpf = _normalize_cpf(payload.cpf)
    email = _normalize_email(payload.email)
    nome = payload.nome.strip()
    cep = _normalize_cep(payload.endereco.cep)
    estado = payload.endereco.estado.strip().upper()

    if len(cpf) != 11:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CPF invalido.")

    if not nome:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome invalido.")

    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="E-mail invalido.")

    if payload.nascimento > date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data de nascimento invalida.",
        )

    if len(cep) != 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CEP invalido.")

    if len(estado) != 2 or not estado.isalpha():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado invalido.")

    duplicate = db.execute(
        select(Usuario.id).where(or_(Usuario.cpf == cpf, Usuario.email == email))
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF ou e-mail ja cadastrado.")

    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha=_hash_password(payload.senha),
        data_nascimento=payload.nascimento,
        cpf=cpf,
        cep=cep,
        logradouro=payload.endereco.logradouro.strip(),
        numero=payload.endereco.numero.strip(),
        bairro=payload.endereco.bairro.strip(),
        cidade=payload.endereco.cidade.strip(),
        estado=estado,
    )

    try:
        db.add(novo_usuario)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ou e-mail ja cadastrado.",
        )

    return {"message": "Cadastro realizado com sucesso."}


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    login_value = payload.cpf.strip()
    if not login_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CPF/e-mail e obrigatorio.",
        )

    if "@" in login_value:
        normalized_login = _normalize_email(login_value)
        lookup = Usuario.email == normalized_login
    else:
        normalized_login = _normalize_cpf(login_value)
        if len(normalized_login) != 11:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CPF invalido.",
            )
        lookup = Usuario.cpf == normalized_login

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