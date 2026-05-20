# Arquitetura do projeto

---

## Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Servidor web | **FastAPI** (Python) |
| Banco de dados | **MySQL** via `mysql-connector-python` |
| Templates HTML | **Jinja2** (sem JavaScript de framework) |
| Frontend JS | **Vanilla JS** com módulos ES6 nativos |
| Autenticação | Sessões armazenadas no banco (cookie HTTP-only) |
| Senhas | **bcrypt** via `passlib` |
| Configuração | Variáveis de ambiente via `.env` + `python-dotenv` |

---

## Estrutura de diretórios

```
server/
│
├── main.py                     ← ponto de entrada: expõe a variável `app`
│
├── core/
│   ├── app.py                  ← constrói o FastAPI app (middlewares, rotas, lifespan)
│   ├── settings.py             ← configurações lidas do .env
│   ├── session.py              ← leitura/gravação do cookie de sessão
│   └── security.py             ← hash_password() e verify_password()
│
├── db/
│   ├── connection.py           ← pool de conexões MySQL + get_db()
│   └── init_db.py              ← CREATE TABLE, migrações e seed inicial
│
├── models/                     ← dataclasses: representam uma linha do banco
│   ├── user.py
│   ├── account.py
│   ├── transaction.py
│   ├── address.py
│   ├── portfolio.py
│   ├── user_portfolio.py
│   ├── manager_portfolio.py
│   └── user_avatar.py
│
├── repositories/               ← queries SQL: toda interação com o banco passa aqui
│   ├── user_repository.py
│   ├── account_repository.py
│   ├── transaction_repository.py
│   ├── address_repository.py
│   ├── session_repository.py
│   ├── portfolio_repository.py
│   ├── user_portfolio_repository.py
│   ├── manager_portfolio_repository.py
│   └── user_avatar_repository.py
│
├── web/
│   ├── router.py               ← agrega todos os routers em um único web_router
│   └── routes/
│       ├── _shared.py          ← templates, require_user(), require_manager(), filtros Jinja
│       ├── login.py            ← GET/POST /login
│       ├── logout.py           ← POST /logout
│       ├── cadastro.py         ← GET/POST /cadastro
│       ├── home.py             ← GET /home, POST /home/abrir-poupanca
│       ├── operacao.py         ← GET/POST /operacao
│       ├── extrato.py          ← GET /extrato
│       ├── perfil.py           ← GET/POST /perfil, /perfil/avatar, /perfil/cpf
│       ├── investimentos.py    ← GET /investimentos
│       ├── manager.py          ← GET /manager
│       ├── manager_accounts.py ← GET /manager/accounts
│       └── manager_select.py   ← GET /manager/select
│
├── templates/
│   ├── base.html               ← layout raiz (CSS global, blocos title/styles/scripts)
│   ├── auth_base.html          ← layout de auth (estende base.html)
│   ├── dashboard_base.html     ← layout do painel (estende base.html, inclui sidebar)
│   ├── login.html
│   ├── cadastro.html
│   ├── home.html
│   ├── operacao.html
│   ├── extrato.html
│   ├── perfil.html
│   ├── investimentos.html
│   ├── manager.html
│   ├── manager_accounts.html
│   └── components/
│       ├── forms.html          ← macro input_field()
│       ├── auth_brand_panel.html
│       ├── dashboard_sidebar.html
│       ├── manager_sidebar.html
│       ├── dashboard_macros.html
│       └── investment_macros.html
│
└── static/
    ├── css/                    ← estilos por página
    └── js/
        ├── components/         ← módulos reutilizáveis
        │   ├── modal.js
        │   ├── form-feedback.js
        │   ├── formatters.js
        │   ├── date-range-picker.js
        │   ├── cep-lookup.js
        │   ├── sidebar.js
        │   ├── ui-cards.js
        │   └── transaction-flow.js
        └── pages/              ← JS específico de cada página
            ├── login.js
            ├── cadastro.js
            ├── home.js
            ├── operacao.js
            ├── extrato.js
            ├── perfil.js
            └── investimentos.js
```

---

## Como o app sobe

```
uvicorn server.main:app
          │
          └─ server/main.py
               └─ create_app()  [server/core/app.py]
                    │
                    ├─ 1. lifespan()
                    │       ├─ check_database_connection()   testa a conexão
                    │       ├─ init_db()                     cria tabelas + migra + seed
                    │       └─ yield  ← app começa a aceitar requisições
                    │
                    ├─ 2. app.add_middleware(SessionRefreshMiddleware)
                    │       └─ renova o cookie de sessão a cada requisição
                    │
                    ├─ 3. app.mount("/static", StaticFiles(...))
                    │       └─ serve arquivos CSS/JS/imagens
                    │
                    └─ 4. app.include_router(web_router)
                            └─ registra todas as rotas HTTP
```

### `server/main.py`
Arquivo mínimo de entrada. Apenas chama `create_app()` e expõe o resultado como `app` — que é o que o uvicorn precisa.

### `server/core/app.py`
É aqui que o app é montado de verdade. Define três coisas:

1. **`lifespan`** — código que roda uma vez na inicialização (antes do primeiro request) e uma vez no encerramento. Checa a conexão com o banco e inicializa as tabelas.
2. **`SessionRefreshMiddleware`** — intercepta toda resposta HTTP e prorroga a sessão do usuário se houver um cookie válido.
3. **`create_app()`** — fábrica que monta o `FastAPI`, registra o middleware, o diretório de static files e o router principal.

### `server/core/settings.py`
Lê variáveis de ambiente do `.env` uma única vez via `@lru_cache`. Configurações disponíveis:

```
APP_NAME, DEBUG
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_POOL_SIZE
SESSION_SECRET, SESSION_TIMEOUT_SECONDS
```

---

## Camadas da arquitetura

O projeto é organizado em 4 camadas verticais. Cada camada só conversa com a camada imediatamente abaixo.

```
┌─────────────────────────────────────┐
│           Templates (.html)         │  ← renderiza HTML para o browser
├─────────────────────────────────────┤
│           Routes (.py)              │  ← recebe request, valida, decide
├─────────────────────────────────────┤
│         Repositories (.py)          │  ← queries SQL, retorna objetos
├─────────────────────────────────────┤
│     Models (dataclasses) + DB       │  ← define a forma dos dados
└─────────────────────────────────────┘
```

### Camada 1 — Modelos (`server/models/`)

Cada modelo é um **`@dataclass`** puro: sem lógica, sem conexão com o banco, só a estrutura dos dados.

```python
@dataclass
class User:
    id: int
    cpf: str
    type: UserType       # Enum: 'client' | 'manager'
    name: str
    email: str
    password: str
    birthday: date
    address_id: int
    created_at: datetime
    updated_at: datetime
    has_avatar: bool = False   # calculado em runtime, não vem do banco
```

Quando o banco retorna uma linha, o repositório converte o dicionário `{"id": 1, "name": "João", ...}` para um objeto `User`. A partir daí, o resto do código trabalha com `user.name`, `user.email`, etc. — nunca com dicionários crús.

**Modelos existentes:**

| Modelo | Tabela | Representa |
|--------|--------|-----------|
| `User` | `users` | Usuário (cliente ou gerente) |
| `Account` | `accounts` | Conta corrente ou poupança |
| `Transaction` | `transactions` | Qualquer movimentação financeira |
| `Address` | `addresses` | Endereço vinculado a um usuário |
| `Portfolio` | `portfolios` | Tipo de investimento disponível |
| `UserPortfolio` | `user_portfolios` | Posição de um usuário num portfólio |
| `ManagerPortfolio` | `manager_portfolios` | Portfólios gerenciados por um gerente |
| `UserAvatar` | `user_avatars` | Foto de perfil (BLOB) |

---

### Camada 2 — Repositórios (`server/repositories/`)

Toda query SQL fica aqui. Nenhuma rota escreve SQL diretamente.

O padrão é sempre o mesmo:

```python
# 1. Função auxiliar converte dict → dataclass
def _row_to_user(row: dict) -> User:
    return User(id=row["id"], name=row["name"], ...)

# 2. Classe com métodos estáticos/de classe
class UserRepository:

    @classmethod
    def get_by_id(cls, db, user_id: int) -> User | None:
        cursor = db.cursor(dictionary=True)   # retorna dicts, não tuplas
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user(row) if row else None

    @classmethod
    def create(cls, db, *, cpf: str, name: str, ...) -> User:
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (...) VALUES (%s, ...)", (...,))
        new_id = cursor.lastrowid   # id gerado pelo AUTO_INCREMENT
        cursor.close()
        return cls.get_by_id(db, new_id)
```

**Regras dos repositórios:**
- Nunca chamam `db.commit()` — quem commita é a **rota**, depois de todas as operações
- Nunca lançam exceções de negócio — só deixam subir erros do banco
- Recebem `db` como primeiro argumento (a conexão vem injetada pelo FastAPI via `get_db`)
- Usam `cursor(dictionary=True)` apenas em SELECTs que precisam mapear campos por nome

---

### Camada 3 — Rotas (`server/web/routes/`)

Cada arquivo de rota define um `APIRouter` com um ou mais endpoints. A rota:

1. Chama `require_user()` (ou `require_manager()`) para verificar autenticação
2. Lê dados do banco via repositórios
3. Valida a entrada (formulários)
4. Chama repositórios para gravar
5. Faz `db.commit()` se houve escrita
6. Renderiza um template ou redireciona

```python
router = APIRouter(tags=["pages"])

@router.get("/home")
def home_page(request: Request, db=Depends(get_db)):
    # 1. Auth
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    # 2. Busca dados
    checking = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)

    # 3. Renderiza
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "user": user, "checking_account": checking},
    )
```

#### `server/web/router.py`

Agrega todos os `APIRouter` individuais em um único `web_router`, que é registrado no `FastAPI` app. Também define o catch-all `/{path:path}` que redireciona URLs desconhecidas para `/home`.

#### `server/web/routes/_shared.py`

Arquivo auxiliar compartilhado por todas as rotas. Define três coisas:

**`templates`** — instância única do `Jinja2Templates`, com filtros e globals registrados:

| Recurso Jinja | Como usar no template | O que faz |
|---------------|-----------------------|-----------|
| `\| brl` | `{{ valor \| brl }}` | Formata número como `R$ 1.234,56` |
| `user_initials(user)` | `{{ user_initials(user) }}` | Retorna `"JD"` para `"João Dias"` |
| `is_manager(user)` | `{% if is_manager(user) %}` | `True` se o usuário é gerente |

**`require_user(request, db)`** — guarda de autenticação:
```
lê cookie → SessionRepository.get_user_id() → UserRepository.get_by_id()
→ retorna User (ok) ou RedirectResponse("/login") (não autenticado)
```
Também popula `user.has_avatar` verificando se existe uma foto de perfil.

**`require_manager(request, db)`** — chama `require_user` e depois verifica se `user.type == MANAGER`. Redireciona para `/home` se for cliente.

---

### Camada 4 — Templates (`server/templates/`)

Os templates usam **Jinja2** e seguem uma hierarquia de herança:

```
base.html
├── auth_base.html
│   ├── login.html
│   └── cadastro.html
└── dashboard_base.html
    ├── home.html
    ├── operacao.html
    ├── extrato.html
    ├── perfil.html
    ├── investimentos.html
    ├── manager.html
    └── manager_accounts.html
```

**`base.html`** define os blocos fundamentais: `title`, `styles`, `scripts`, `content`.

**`auth_base.html`** estende `base.html` e adiciona o layout de duas colunas das páginas de login/cadastro (painel de marca + formulário).

**`dashboard_base.html`** estende `base.html` e inclui o sidebar, topbar, e o container do painel. Os templates filhos preenchem `dashboard_content` e `dashboard_scripts`.

**`components/forms.html`** define a macro `input_field`:
```jinja
{{ input_field('email', 'E-mail', 'email', 'email', value=(form.email | default(''))) }}
{#              nome     label     tipo     autocomplete  valor atual              #}
```

---

## Banco de dados

### Conexão (`server/db/connection.py`)

O projeto usa um **connection pool** — um conjunto de conexões pré-abertas reaproveitadas a cada request, evitando o overhead de abrir uma conexão nova a cada chamada.

```
Requisição HTTP chegou
    → FastAPI chama get_db()  [Depends(get_db)]
        → _get_pool().get_connection()  pega uma conexão do pool
        → yield conn             a rota usa a conexão
        → conn.rollback()        desfaz qualquer coisa não commitada (segurança)
        → conn.close()           devolve a conexão ao pool
```

`get_db()` é um **generator** usado como dependência do FastAPI (`Depends(get_db)`). O `yield` separa o setup (pegar a conexão) do teardown (devolver ao pool), garantindo que a conexão sempre volte mesmo se a rota lançar uma exceção.

### Schema (`server/db/init_db.py`)

Chamado uma vez no startup via `lifespan`. Três funções:

**`_create_tables(conn)`** — executa `CREATE TABLE IF NOT EXISTS` para todas as 9 tabelas. A ordem importa: tabelas com `FOREIGN KEY` devem vir depois das tabelas que elas referenciam.

```
addresses → users → accounts → transactions
                             → sessions
                             → user_avatars
portfolios → manager_portfolios
           → user_portfolios
```

**`_apply_migrations(conn)`** — contém `ALTER TABLE` para mudanças em bancos já existentes. Cada alteração é guardada por uma verificação (`_column_exists` ou `_enum_has_value`) para ser idempotente — pode rodar N vezes sem causar erro ou duplicar dados.

**`_seed_default_users_if_empty(conn)`** — se a tabela `users` estiver vazia, cria um gerente e um cliente padrão com senhas pré-definidas para facilitar o desenvolvimento.

### Tabelas

```
addresses         id, cep, street, state, city, neighborhood, number
users             id, cpf*, type, name, email*, password, birthday, address_id→addresses
accounts          id, user_id→users, type, account_number*, agency, balance
transactions      id, type, from_account_id→accounts, to_account_id→accounts, amount, description
sessions          id (token hex-64)*, user_id→users, expires_at, ip_address, user_agent
portfolios        id, name, stock_code, stock_name, stock_price
user_portfolios   id, portfolio_id→portfolios, user_id→users, stock_amount
manager_portfolios id, portfolio_id→portfolios, manager_id→users
user_avatars      id, user_id→users*, image_data (BLOB), mime_type

* = UNIQUE
```

---

## Fluxo completo de uma requisição

Exemplo: usuário logado acessa `/home`.

```
Browser
  │
  │  GET /home
  │  Cookie: session_id=abc123
  │
  ▼
FastAPI recebe a requisição
  │
  ├─ SessionRefreshMiddleware.dispatch()  [antes de processar]
  │    └─ (ainda não sabe se a sessão é válida, só renova depois)
  │
  ├─ web_router roteia para home.home_page()
  │
  ├─ get_db()  [Depends]
  │    └─ pega uma conexão do pool, passa como `db`
  │
  └─ home_page(request, db) executa:
        │
        ├─ require_user(request, db)
        │    ├─ get_session_token(request)  → "abc123"
        │    ├─ SessionRepository.get_user_id(db, "abc123")  → 7
        │    ├─ UserRepository.get_by_id(db, 7)  → User(id=7, name="João", ...)
        │    └─ retorna o User
        │
        ├─ AccountRepository.get_by_user_and_type(db, 7, CHECKING)  → Account(balance=500)
        ├─ AccountRepository.get_by_user_and_type(db, 7, SAVINGS)   → Account(balance=200)
        │
        └─ templates.TemplateResponse("home.html", context={user, checking_account, ...})
              │
              └─ Jinja2 renderiza home.html
                    └─ {% extends "dashboard_base.html" %}
                          └─ inclui sidebar, topbar, injeta user.name, account.balance | brl
  │
  │  [depois de processar]
  ├─ SessionRefreshMiddleware.dispatch()  continua
  │    └─ token existe? → SessionRepository.refresh()  → atualiza expires_at no banco
  │    └─ response.set_cookie(session_id=abc123, max_age=300)  renova o cookie
  │
  ▼
Browser recebe 200 HTML + cookie renovado
```

---

## Sistema de sessões

Diferente do padrão mais simples de guardar dados no cookie, este projeto guarda **apenas um token** no cookie e os dados da sessão ficam na tabela `sessions` do banco:

```
Cookie do browser:   session_id = "a3f9c2e1..."   (64 chars hex)
                                        │
                                        ▼
Tabela sessions:   id="a3f9c2e1...",  user_id=7,  expires_at="2026-05-20 15:30:00"
```

Vantagens:
- O servidor pode invalidar sessões imediatamente (logout real)
- É possível listar todos os devices logados por usuário
- O cookie em si não contém nenhuma informação sensível

O middleware `SessionRefreshMiddleware` renova o `expires_at` e o `max_age` do cookie a cada requisição, fazendo a sessão durar enquanto o usuário continuar ativo.

---

## JavaScript

O JS do projeto é **vanilla** (sem React, Vue ou bundler). Cada página carrega seu próprio arquivo de `pages/` via `<script type="module">`, que por sua vez importa componentes de `components/`:

```javascript
// pages/cadastro.js
import { initCepLookup } from "../components/cep-lookup.js";
import { formatCPF }     from "../components/formatters.js";

initCepLookup();
```

Componentes reutilizáveis:

| Componente | Função |
|-----------|--------|
| `formatters.js` | Máscara de CPF, CEP, valor monetário |
| `cep-lookup.js` | Preenche endereço automaticamente via API ViaCEP |
| `modal.js` | Abre/fecha modais de confirmação |
| `form-feedback.js` | Exibe erros em campos específicos do formulário |
| `sidebar.js` | Abre/fecha o menu lateral no mobile |
| `transaction-flow.js` | Troca o formulário visível na página de operações |
| `date-range-picker.js` | Seletor de período de datas no extrato |

---

## Onde fica cada responsabilidade

| Responsabilidade | Onde fica |
|-----------------|-----------|
| Inicializar o banco na subida | `server/db/init_db.py` → `lifespan` em `app.py` |
| Definir configurações | `server/core/settings.py` + `.env` |
| Conectar ao banco | `server/db/connection.py` → `get_db()` |
| Definir a forma dos dados | `server/models/` |
| Ler e gravar no banco | `server/repositories/` |
| Verificar se está logado | `server/web/routes/_shared.py` → `require_user()` |
| Gravar/ler o cookie de sessão | `server/core/session.py` |
| Lógica de cada página | `server/web/routes/` |
| Renderizar HTML | `server/templates/` |
| Formatar valores na view | `_shared.py` → filtros Jinja (`brl`, etc.) |
| Interatividade no browser | `server/static/js/` |
| Hash e verificação de senha | `server/core/security.py` |
