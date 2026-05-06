from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["pages"])


@router.get("/")
def index():
    return RedirectResponse(url="/home")
