from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.api.router import api_router
from server.core.settings import get_settings
from server.db.connection import check_database_connection
from server.db.init_db import init_db
from server.web.router import web_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_database_connection()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    base_dir = Path(__file__).resolve().parents[1]

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")
    
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")
    return app
