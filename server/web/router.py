from fastapi import APIRouter

from server.web.routes.cadastro import router as cadastro_router
from server.web.routes.extrato import router as extrato_router
from server.web.routes.healthcheck import router as healthcheck_router
from server.web.routes.home import router as home_router
from server.web.routes.index import router as index_router
from server.web.routes.investimentos import router as investimentos_router
from server.web.routes.login import router as login_router
from server.web.routes.manager import router as manager_router
from server.web.routes.manager_accounts import router as manager_accounts_router
from server.web.routes.transacao import router as transacao_router

web_router = APIRouter()
web_router.include_router(index_router)
web_router.include_router(home_router)
web_router.include_router(transacao_router)
web_router.include_router(investimentos_router)
web_router.include_router(extrato_router)
web_router.include_router(login_router)
web_router.include_router(cadastro_router)
web_router.include_router(manager_router)
web_router.include_router(manager_accounts_router)
web_router.include_router(healthcheck_router)
