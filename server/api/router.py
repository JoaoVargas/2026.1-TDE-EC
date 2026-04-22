from fastapi import APIRouter

from server.api.routes.auth import router as auth_router
from server.api.routes.health import router as health_router
from server.api.routes.management import router as management_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(management_router)
