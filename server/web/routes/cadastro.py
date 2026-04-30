import re
from datetime import date

import mysql.connector.errors
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.core.security import hash_password
from server.core.session import get_session_user_id
from server.db.connection import get_db
from server.repositories.address_repository import AddressRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _only_digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


@router.get("/cadastro")
def cadastro_page(request: Request):
    if get_session_user_id(request):
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="cadastro.html",
        context={"request": request},
    )


@router.post("/cadastro")
async def cadastro_submit(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    cpf: str = Form(...),
    nascimento: str = Form(...),
    senha: str = Form(...),
    confirmar: str = Form(...),
    cep: str = Form(...),
    logradouro: str = Form(...),
    numero: str = Form(...),
    bairro: str = Form(...),
    cidade: str = Form(...),
    estado: str = Form(...),
    db=Depends(get_db),
):
    cpf_digits = _only_digits(cpf)
    cep_digits = _only_digits(cep)
    email_norm = email.strip().lower()
    name_norm = nome.strip()
    state_norm = estado.strip().upper()

    form_ctx = {
        "nome": nome, "email": email, "cpf": cpf, "nascimento": nascimento,
        "cep": cep, "logradouro": logradouro, "numero": numero,
        "bairro": bairro, "cidade": cidade, "estado": estado,
    }

    error = None
    if not name_norm or len(name_norm) < 3:
        error = "Nome deve ter pelo menos 3 caracteres."
    elif not _EMAIL_RE.match(email_norm):
        error = "E-mail inválido."
    elif len(cpf_digits) != 11:
        error = "CPF inválido."
    elif len(senha) < 8:
        error = "Senha deve ter pelo menos 8 caracteres."
    elif senha != confirmar:
        error = "As senhas não coincidem."
    elif len(cep_digits) != 8:
        error = "CEP inválido."
    elif len(state_norm) != 2 or not state_norm.isalpha():
        error = "Estado inválido (use a sigla, ex: PR)."
    else:
        try:
            bday = date.fromisoformat(nascimento)
            if bday > date.today():
                error = "Data de nascimento inválida."
        except ValueError:
            error = "Data de nascimento inválida."

    if not error and UserRepository.exists_by_cpf_or_email(db, cpf=cpf_digits, email=email_norm):
        error = "CPF ou e-mail já cadastrado."

    if error:
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={"request": request, "error": error, "form": form_ctx},
            status_code=422,
        )

    address = AddressRepository.create(
        db,
        cep=cep_digits,
        street=logradouro.strip(),
        state=state_norm,
        city=cidade.strip(),
        neighborhood=bairro.strip(),
        number=numero.strip(),
    )

    try:
        UserRepository.create(
            db,
            cpf=cpf_digits,
            name=name_norm,
            email=email_norm,
            password_hash=hash_password(senha),
            birthday=date.fromisoformat(nascimento),
            address_id=address.id,
        )
        db.commit()
    except mysql.connector.errors.IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="cadastro.html",
            context={"request": request, "error": "CPF ou e-mail já cadastrado.", "form": form_ctx},
            status_code=409,
        )

    return RedirectResponse("/login", status_code=302)
