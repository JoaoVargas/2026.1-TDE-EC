from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from starlette.exceptions import HTTPException as StarletteHTTPException

from server.models.example import fetch_all_from_table

app = FastAPI()

# Libera o frontend acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "server" / "templates"))


# ─── Models ───────────────────────────────────────────────────────────────────

class Endereco(BaseModel):
    cep: str
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    estado: str

class CadastroRequest(BaseModel):
    nome: str
    email: str
    cpf: str
    nascimento: str
    senha: str
    endereco: Endereco

class LoginRequest(BaseModel):
    cpf: str
    senha: str


# ─── Rotas ────────────────────────────────────────────────────────────────────

@app.get("/")
def get_root():
    return {"message": "API online"}


@app.post("/cadastro")
def post_cadastro(dados: CadastroRequest):
    print(f"Novo cadastro: {dados.nome} | CPF: {dados.cpf}")

    # TODO: salvar no banco de dados

    return {"message": "Cadastro realizado com sucesso!"}


@app.post("/login")
def post_login(dados: LoginRequest):
    print(f"Tentativa de login: CPF {dados.cpf}")

    # TODO: verificar no banco de dados

    return {"message": "Login realizado com sucesso!"}


@app.get("/cadastro", response_class=HTMLResponse)
def get_cadastro(request: Request):
    return templates.TemplateResponse(
        request,
        name="cadastro.html",
        context={"request": request},
    )


@app.get("/home", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse(
        request,
        name="home.html",
        context={"request": request},
    )


@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(
        request,
        name="login.html",
        context={"request": request},
    )


@app.get("/investimentos", response_class=HTMLResponse)
def get_investimentos(request: Request):
    return templates.TemplateResponse(
        request,
        name="investimentos.html",
        context={"request": request},
    )


@app.get("/investimentos2", response_class=HTMLResponse)
def get_investimentos2(request: Request):
    return templates.TemplateResponse(
        request,
        name="investimentos2.html",
        context={"request": request},
    )


@app.get("/transacao", response_class=HTMLResponse)
def get_transacao(request: Request):
    return templates.TemplateResponse(
        request,
        name="transacao.html",
        context={"request": request},
    )


@app.get("/transacao2", response_class=HTMLResponse)
def get_transacao2(request: Request):
    return templates.TemplateResponse(
        request,
        name="transacao2.html",
        context={"request": request},
    )


@app.get("/table/{name}", response_class=HTMLResponse)
def get_table(request: Request, name: str):
    table_data = fetch_all_from_table(name)

    return templates.TemplateResponse(
        request,
        name="table.html",
        context={"request": request, "name": name, "table_data": table_data}
    )

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return RedirectResponse(url="/home", status_code=307)
    raise exc

if __name__ == "__main__":
    import uvicorn

    project_root = Path(__file__).resolve().parents[1]
    uvicorn.run(
        "server.main:app",
        host="localhost",
        port=8000,
        reload=True,
        app_dir=str(project_root),
    )

