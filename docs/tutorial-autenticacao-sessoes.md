# Tutorial: Autenticação e sessões

> Como o sistema sabe quem está logado, como proteger páginas e como
> fazer login/logout.

---

## Como a autenticação funciona

O sistema usa **sessões armazenadas no banco de dados**. Nenhum dado de usuário fica em cookie — apenas um token aleatório.

```
Browser                          Servidor                       Banco
  │                                 │                              │
  │── POST /login (cpf + senha) ───►│                              │
  │                                 │── SELECT users WHERE... ────►│
  │                                 │◄── user row ─────────────────│
  │                                 │── verify_password() ─────────│
  │                                 │── INSERT INTO sessions... ───►│
  │◄── Set-Cookie: session_id=TOKEN─│                              │
  │                                 │                              │
  │── GET /home (Cookie: TOKEN) ───►│                              │
  │                                 │── SELECT sessions WHERE... ──►│
  │                                 │◄── user_id ──────────────────│
  │                                 │── SELECT users WHERE id... ──►│
  │◄── 200 HTML (página do usuário)─│                              │
```

---

## Peças do sistema de sessões

### `server/core/session.py` — gerencia o cookie

| Função | O que faz |
|--------|-----------|
| `set_session_user(response, token)` | Grava o token no cookie HTTP-only |
| `clear_session(response)` | Remove o cookie (logout) |
| `get_session_token(request)` | Lê o token do cookie da requisição |
| `get_session_user_id(request, db)` | Lê o token → consulta `sessions` → retorna `user_id` ou `None` |

### `server/repositories/session_repository.py` — gerencia a tabela `sessions`

| Método | O que faz |
|--------|-----------|
| `create(db, user_id, expires_at, ip, user_agent)` | Insere nova sessão, retorna o token |
| `get_user_id(db, token)` | Consulta sessão válida, retorna `user_id` ou `None` |
| `delete(db, token)` | Remove a sessão (logout) |
| `refresh(db, token, new_expires_at)` | Prorroga a expiração da sessão |
| `cleanup_expired(db)` | Remove sessões vencidas (chamado periodicamente) |

### `server/core/security.py` — senhas

| Função | O que faz |
|--------|-----------|
| `hash_password(plain)` | Retorna hash bcrypt da senha |
| `verify_password(plain, hashed)` | Retorna `True` se a senha bate com o hash |

---

## Como o login funciona

**Arquivo:** `server/web/routes/login.py`

```python
@router.post("/login")
async def login_submit(
    request: Request,
    login: str = Form(...),   # CPF ou e-mail
    senha: str = Form(...),
    db=Depends(get_db),
):
    # 1. Busca o usuário por CPF ou e-mail
    user = UserRepository.get_by_login(db, login)

    # 2. Verifica a senha
    if not user or not verify_password(senha, user.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request": request, "error": "CPF/e-mail ou senha inválidos."},
            status_code=401,
        )

    # 3. Cria a sessão no banco
    token = SessionRepository.create(
        db,
        user_id=user.id,
        expires_at=datetime.now() + timedelta(hours=8),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    # 4. Grava o token no cookie e redireciona
    response = RedirectResponse("/home", status_code=302)
    set_session_user(response, token)
    return response
```

---

## Como o logout funciona

**Arquivo:** `server/web/routes/logout.py`

```python
@router.post("/logout")
async def logout(request: Request, db=Depends(get_db)):
    token = get_session_token(request)
    if token:
        SessionRepository.delete(db, token)
        db.commit()

    response = RedirectResponse("/login", status_code=302)
    clear_session(response)
    return response
```

---

## Como proteger uma rota

### Proteger para qualquer usuário logado

```python
from server.web.routes._shared import require_user

@router.get("/minha-pagina")
def minha_pagina(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result   # ← não logado: redireciona para /login
    user = result       # ← logado: user é o objeto User
    ...
```

### Proteger para gerentes apenas

```python
from server.web.routes._shared import require_manager

@router.get("/manager/relatorios")
def relatorios(request: Request, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result   # ← não logado OU não é gerente
    user = result
    ...
```

### Como `require_user` e `require_manager` funcionam

**Arquivo:** `server/web/routes/_shared.py`

```python
def require_user(request: Request, db) -> User | RedirectResponse:
    user_id = get_session_user_id(request, db)
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return user


def require_manager(request: Request, db) -> User | RedirectResponse:
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    if result.type != UserType.MANAGER:
        return RedirectResponse("/home", status_code=302)
    return result
```

> **O padrão `isinstance(result, RedirectResponse)`** é necessário porque a função pode retornar dois tipos diferentes: um `User` (sucesso) ou um `RedirectResponse` (falha). Sempre verifique antes de usar `result` como usuário.

---

## Auto-renovação da sessão

O middleware `SessionRefreshMiddleware` em `server/app.py` renova a sessão automaticamente a cada requisição:

```python
class SessionRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        token = get_session_token(request)
        if token:
            # Prorroga a sessão por mais 8 horas a partir de agora
            SessionRepository.refresh(db, token, datetime.now() + timedelta(hours=8))
        return response
```

Isso significa que enquanto o usuário continua usando o sistema, a sessão nunca expira. Ela só expira após **8 horas de inatividade**.

---

## Tabela `sessions` no banco

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id          CHAR(64)     NOT NULL PRIMARY KEY,   -- token hex de 64 chars
    user_id     INT          NOT NULL,
    expires_at  DATETIME     NOT NULL,
    ip_address  VARCHAR(45)  NULL,
    user_agent  VARCHAR(512) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

O `ON DELETE CASCADE` garante que se um usuário for deletado, todas as suas sessões também são removidas automaticamente.

---

## Casos de uso comuns

### Saber qual usuário está logado sem proteção obrigatória

```python
from server.core.session import get_session_user_id
from server.repositories.user_repository import UserRepository

user_id = get_session_user_id(request, db)
user = UserRepository.get_by_id(db, user_id) if user_id else None
# user é None se não estiver logado, User se estiver
```

### Redirecionar usuário já logado para fora da página de login

```python
@router.get("/login")
def login_page(request: Request, db=Depends(get_db)):
    if get_session_user_id(request, db):
        return RedirectResponse("/home", status_code=302)
    return templates.TemplateResponse(...)
```

### Forçar logout de todos os dispositivos de um usuário

```python
SessionRepository.delete_by_user(db, user_id=user.id)
db.commit()
```

### Criar um usuário gerente via código (ex: seed)

```python
from server.core.security import hash_password
from server.models.user import UserType

UserRepository.create(
    db,
    cpf="12345678901",
    type=UserType.MANAGER,
    name="Admin",
    email="admin@banco.com",
    password_hash=hash_password("SenhaForte123"),
    birthday=date(1990, 1, 1),
    address_id=address.id,
)
db.commit()
```

---

## Fluxo completo resumido

```
Login
  POST /login
    → get_by_login()       busca user por CPF ou email
    → verify_password()    confere bcrypt
    → SessionRepository.create()  grava na tabela sessions
    → set_session_user()   grava token no cookie
    → redirect

A cada requisição
  SessionRefreshMiddleware
    → lê cookie
    → SessionRepository.refresh()  renova expires_at

Acesso a página protegida
  require_user()
    → get_session_token()  lê cookie
    → SessionRepository.get_user_id()  valida no banco
    → UserRepository.get_by_id()  carrega o usuário
    → retorna User ou RedirectResponse("/login")

Logout
  POST /logout
    → SessionRepository.delete()  remove do banco
    → clear_session()  remove o cookie
    → redirect /login
```
