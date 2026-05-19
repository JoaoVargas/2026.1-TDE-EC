from fastapi import APIRouter, Depends, File, Request, UploadFile, Form
from fastapi.responses import RedirectResponse, Response

from server.db.connection import get_db
from server.repositories.address_repository import AddressRepository
from server.repositories.user_avatar_repository import UserAvatarRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])

_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_AVATAR_BYTES = 4 * 1024 * 1024  # 4 MB

_ERROR_MESSAGES = {
    "tipo_invalido": "Formato de imagem inválido. Use JPEG, PNG, WEBP ou GIF.",
    "arquivo_grande": "Imagem muito grande. O limite é 4 MB.",
    "arquivo_vazio": "Selecione um arquivo de imagem.",
    "dados_invalidos": "Nome ou email inválido.",
    "endereco_invalido": "Endereço inválido. Verifique os campos.",
}

_FLASH_MESSAGES = {
    "foto_atualizada": "Foto de perfil atualizada com sucesso.",
    "foto_removida": "Foto de perfil removida.",
    "dados_atualizados": "Dados atualizados com sucesso.",
    "endereco_atualizado": "Endereço atualizado com sucesso.",
}


@router.get("/perfil")
def perfil_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    address = AddressRepository.get_by_id(db, user.address_id)

    error_key = request.query_params.get("error")
    flash_key = request.query_params.get("flash")

    return templates.TemplateResponse(
        request=request,
        name="perfil.html",
        context={
            "request": request,
            "active_page": "perfil",
            "dashboard_label": "Meu perfil",
            "user": user,
            "address": address,
            "has_avatar": user.has_avatar,
            "error": _ERROR_MESSAGES.get(error_key) if error_key else None,
            "flash": _FLASH_MESSAGES.get(flash_key) if flash_key else None,
        },
    )


@router.get("/perfil/dados")
def perfil_dados(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    address = AddressRepository.get_by_id(db, user.address_id)

    return {
        "name": user.name,
        "email": user.email,
        "cpf": user.cpf,
        "cep": address.cep if address else "",
        "street": address.street if address else "",
        "state": address.state if address else "",
        "city": address.city if address else "",
        "neighborhood": address.neighborhood if address else "",
        "number": address.number if address else "",
    }


@router.post("/perfil/nome")
async def update_perfil_nome(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    name = name.strip()
    email = email.strip()
    if not name or len(name) < 3 or not email or "@" not in email:
        return RedirectResponse(url="/perfil?error=dados_invalidos", status_code=303)

    UserRepository.update_profile(db, user_id=user.id, name=name, email=email)
    db.commit()
    return RedirectResponse(url="/perfil?flash=dados_atualizados", status_code=303)


@router.post("/perfil/endereco")
async def update_perfil_endereco(
    request: Request,
    cep: str = Form(...),
    street: str = Form(...),
    state: str = Form(...),
    city: str = Form(...),
    neighborhood: str = Form(...),
    number: str = Form(...),
    db=Depends(get_db)
    ):

    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result
    
    cep_clean = "".join(c for c in cep if c.isdigit())
    if not all([cep_clean, street.strip(), state.strip(), city.strip(), neighborhood.strip(), number.strip()]) or len(cep_clean) != 8:
        return RedirectResponse(url="/perfil?error=endereco_invalido", status_code=303)

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
    return RedirectResponse(url="/perfil?flash=endereco_atualizado", status_code=303)


@router.post("/perfil/avatar")
async def perfil_avatar_upload(
    request: Request,
    avatar: UploadFile = File(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    data = await avatar.read()

    if not data:
        return RedirectResponse("/perfil?error=arquivo_vazio", status_code=303)

    if len(data) > _MAX_AVATAR_BYTES:
        return RedirectResponse("/perfil?error=arquivo_grande", status_code=303)

    mime_type = (avatar.content_type or "").lower()
    if mime_type not in _ALLOWED_MIME_TYPES:
        return RedirectResponse("/perfil?error=tipo_invalido", status_code=303)

    UserAvatarRepository.upsert(db, user_id=user.id, image_data=data, mime_type=mime_type)
    db.commit()

    return RedirectResponse("/perfil?flash=foto_atualizada", status_code=303)


@router.post("/perfil/avatar/remover")
def perfil_avatar_remove(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    UserAvatarRepository.delete(db, user.id)
    db.commit()

    return RedirectResponse("/perfil?flash=foto_removida", status_code=303)


@router.get("/perfil/avatar/{user_id}")
def perfil_avatar_serve(user_id: int, db=Depends(get_db)):
    avatar = UserAvatarRepository.get_by_user_id(db, user_id)
    if not avatar:
        return Response(status_code=404)
    return Response(
        content=avatar.image_data,
        media_type=avatar.mime_type,
        headers={"Cache-Control": "private, max-age=60"},
    )
