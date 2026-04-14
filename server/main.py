import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.auth import criar_token, verificar_token
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Any, Mapping, cast
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
import mysql.connector

from models.usuarios import criar_usuario, autenticar_usuario, usuario_existe
from models.example import fetch_all_from_table

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

app.mount("/styles", StaticFiles(directory=str(BASE_DIR / "server" / "styles")), name="styles")
app.mount("/requisições", StaticFiles(directory=str(BASE_DIR / "server" / "requisições")), name="requisicoes")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "server" / "static")), name="static")

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
    
@app.get("/verificar")
def get_verificar(cpf: str = None, email: str = None):
    existe = usuario_existe(cpf=cpf, email=email)
    return {"disponivel": not existe}

@app.get("/extrato", response_class=HTMLResponse)
def get_extrato(request: Request):
    return templates.TemplateResponse(request, name="extrato.html", context={"request": request})


@app.post("/cadastro")
def post_cadastro(dados: CadastroRequest):
    print(f"Novo cadastro: {dados.nome} | CPF: {dados.cpf}")

    try:
        usuario_id = criar_usuario(dados.model_dump())
        return {"message": "Cadastro realizado com sucesso!", "usuario_id": usuario_id}
    except ValueError:
        raise HTTPException(status_code=400, detail="Data de nascimento inválida. Use YYYY-MM-DD.")
    except mysql.connector.Error as e:
        if e.errno == 1062:
            raise HTTPException(status_code=409, detail="CPF ou e-mail já cadastrado.")
        raise HTTPException(status_code=500, detail="Erro ao salvar usuário no banco.")


@app.post("/login")
def post_login(dados: LoginRequest):
    cpf_limpo = "".join(filter(str.isdigit, dados.cpf))

    if len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido.")

    try:
        usuario = autenticar_usuario(cpf_limpo, dados.senha)
    except mysql.connector.Error:
        raise HTTPException(status_code=500, detail="Erro ao consultar usuário.")

    if not usuario:
        raise HTTPException(status_code=401, detail="CPF ou senha incorretos.")

    token = criar_token({
        "id": usuario["id"],
        "nome": usuario["nome"],
        "cpf": usuario["cpf"],
    })

    return {
        "message": "Login realizado com sucesso!",
        "token": token,
        "usuario": usuario,
    }

@app.get("/me")
def get_me(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido.")

    token = authorization.split(" ")[1]
    payload = verificar_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    return payload


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
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
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

