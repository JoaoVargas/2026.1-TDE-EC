from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.core.security import verify_password
from server.core.session import get_session_user_id, set_session_user
from server.db.connection import get_db
from server.models.user import UserType
from server.repositories.session_repository import SessionRepository
from server.repositories.user_repository import UserRepository
from server.web.routes._shared import templates

router = APIRouter(tags=["pages"])


@router.get("/login")
def login_page(request: Request, db=Depends(get_db)):
    if get_session_user_id(request, db):
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    cpf: str = Form(...),
    senha: str = Form(...),
    db=Depends(get_db),
):
    login_value = cpf.strip()
    error = None

    if not login_value:
        error = "CPF ou e-mail é obrigatório."
    elif not senha:
        error = "Senha é obrigatória."
    else:
        user = UserRepository.get_by_login(db, login_value)
        if not user or not verify_password(senha, user.password):
            error = "CPF/e-mail ou senha incorretos."

    if error:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request": request, "error": error, "cpf_value": cpf},
            status_code=422,
        )

    SessionRepository.cleanup_expired(db)
    role = user.type.value if hasattr(user.type, "value") else str(user.type)
    redirect_to = "/manager/select" if role == UserType.MANAGER.value else "/home"
    response = RedirectResponse(redirect_to, status_code=302)
    set_session_user(
        response,
        db,
        user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return response
