from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.address_repository import AddressRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import require_user

router = APIRouter(tags=["pages"])

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
async def update_perfil_nome(request: Request, name: str = Form(...), db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    if not name or len(name) < 3:
        return RedirectResponse(url="/?feedback=nome_invalido", status_code=303)
    
    UserRepository.update_name(db, user_id=user.id, name=name)
    db.commit()
    return RedirectResponse(url="/?feedback=nome_atualizado", status_code=303)

@router.post("/perfil/endereco")
async def update_perfil_endereço(
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
    
    if not cep or not street or not state or not city or not neighborhood or not number:
        return RedirectResponse(url="/?feedback=endereco_invalido", status_code=303)
    
    if len(cep) != 8 or not cep.isdigit():
        return RedirectResponse(url="/?feedback=endereco_invalido", status_code=303)
    
    AddressRepository.update(
        db,
        address_id=user.address_id,
        cep=cep, street=street,
        state=state, city=city,
        neighborhood=neighborhood,
        number=number
        )
    db.commit()
    return RedirectResponse(url="/?feedback=endereco_atualizado", status_code=303)