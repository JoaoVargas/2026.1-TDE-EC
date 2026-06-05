from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from server.web.routes.cadastro import router as cadastro_router
from server.web.routes.cartao import router as cartao_router
from server.web.routes.extrato import router as extrato_router
from server.web.routes.home import router as home_router
from server.web.routes.investimentos import router as investimentos_router
from server.web.routes.login import router as login_router
from server.web.routes.logout import router as logout_router
from server.web.routes.manager import router as manager_router
from server.web.routes.manager_accounts import router as manager_accounts_router
from server.web.routes.manager_cartoes import router as manager_cartoes_router
from server.web.routes.manager_investimentos import router as manager_investimentos_router
from server.web.routes.manager_select import router as manager_select_router
from server.web.routes.operacao import router as operacao_router
from server.web.routes.perfil import router as perfil_router

web_router = APIRouter()
web_router.include_router(login_router)
web_router.include_router(logout_router)
web_router.include_router(cadastro_router)
web_router.include_router(home_router)
web_router.include_router(operacao_router)
web_router.include_router(cartao_router)
web_router.include_router(investimentos_router)
web_router.include_router(extrato_router)
web_router.include_router(manager_router)
web_router.include_router(manager_accounts_router)
web_router.include_router(manager_cartoes_router)
web_router.include_router(manager_investimentos_router)
web_router.include_router(manager_select_router)
web_router.include_router(perfil_router)


@web_router.get("/{path:path}")
def catch_all():
    return RedirectResponse(url="/home")
