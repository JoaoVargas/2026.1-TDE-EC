from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.example import fetch_all_from_table

app = FastAPI()

# Libera o frontend acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="./templates")


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


@app.get("/test/{name}")
def get_test_param(request: Request, name: str):
    data = fetch_all_from_table(name)
    print(f"Fetched data from table '{name}': {data}")
    return templates.TemplateResponse(
        request,
        name="table.html",
        context={"request": request, "name": name, "data": data},
    )