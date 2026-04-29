from datetime import date, datetime, timedelta, timezone
import re

import mysql.connector.errors
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from server.core.security import hash_password, verify_password
from server.core.settings import get_settings
from server.db.connection import get_db
from server.models.user import User, UserType
from server.repositories.address_repository import AddressRepository
from server.repositories.user_repository import UserRepository

router = APIRouter(tags=["auth"])
security = HTTPBearer(auto_error=False)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AddressPayload(BaseModel):
    cep: str = Field(min_length=8, max_length=9)
    street: str
    number: str
    neighborhood: str
    city: str
    state: str = Field(min_length=2, max_length=2)


class RegisterPayload(BaseModel):
    name: str
    email: str
    cpf: str
    birthday: date
    password: str = Field(min_length=8)
    address: AddressPayload


class LoginPayload(BaseModel):
    cpf: str
    password: str


def _normalize_cpf(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _normalize_cep(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _user_type_value(user: User) -> str:
    t = user.type
    return t.value if hasattr(t, "value") else str(t)


def _is_manager(user: User) -> bool:
    return _user_type_value(user) == UserType.MANAGER.value


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
    db=Depends(get_db),
) -> User:
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

    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario nao encontrado.")

    return user


def get_current_manager_user(current_user: User = Depends(get_current_user)) -> User:
    if not _is_manager(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para gerentes.",
        )
    return current_user


@router.get("/verificar")
def verificar_disponibilidade(
    cpf: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db=Depends(get_db),
) -> dict[str, bool]:
    if not cpf and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe cpf ou email para verificacao.",
        )

    existe = UserRepository.exists_by_cpf_or_email(db, cpf=cpf, email=email)
    return {"disponivel": not existe}


@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(payload: RegisterPayload, db=Depends(get_db)) -> dict[str, str]:
    cpf = _normalize_cpf(payload.cpf)
    email = _normalize_email(payload.email)
    name = payload.name.strip()
    cep = _normalize_cep(payload.address.cep)
    state = payload.address.state.strip().upper()

    if len(cpf) != 11:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CPF invalido.")

    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nome invalido.")

    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="E-mail invalido.")

    if payload.birthday > date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data de nascimento invalida.",
        )

    if len(cep) != 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CEP invalido.")

    if len(state) != 2 or not state.isalpha():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Estado invalido.")

    if UserRepository.exists_by_cpf_or_email(db, cpf=cpf, email=email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF ou e-mail ja cadastrado.")

    address = AddressRepository.create(
        db,
        cep=cep,
        street=payload.address.street.strip(),
        state=state,
        city=payload.address.city.strip(),
        neighborhood=payload.address.neighborhood.strip(),
        number=payload.address.number.strip(),
    )

    UserRepository.create(
        db,
        cpf=cpf,
        name=name,
        email=email,
        password_hash=hash_password(payload.password),
        birthday=payload.birthday,
        address_id=address.id,
    )

    try:
        db.commit()
    except mysql.connector.errors.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF ou e-mail ja cadastrado.",
        )

    return {"message": "Cadastro realizado com sucesso."}


@router.post("/login")
def login(payload: LoginPayload, db=Depends(get_db)) -> dict[str, object]:
    login_value = payload.cpf.strip()
    if not login_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CPF/e-mail e obrigatorio.",
        )

    if "@" not in login_value and len(_normalize_cpf(login_value)) != 11:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CPF invalido.",
        )

    user = UserRepository.get_by_login(db, login_value)

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF/e-mail ou senha incorretos.",
        )

    token = _create_access_token(str(user.id))
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "cpf": user.cpf,
            "type": _user_type_value(user),
        },
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)) -> dict[str, object]:
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "cpf": current_user.cpf,
        "type": _user_type_value(current_user),
    }
