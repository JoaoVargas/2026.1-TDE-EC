from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

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


@app.get("/cadastro")
def get_cadastro(request: Request):
    return templates.TemplateResponse(
        request,
        name="cadastro.html",
        context={"request": request},
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

