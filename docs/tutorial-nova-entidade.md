# Tutorial: Adicionando uma nova entidade ao sistema

> Exemplo usado: entidade `Ticket` — um suporte que um cliente abre para o banco.
> Tabela: `tickets` | Campos: id, user_id, subject, message, status, created_at

---

## Visão geral

Uma entidade completa passa por **4 camadas**:

```
Banco de dados  →  Modelo Python  →  Repositório  →  Rota / Template
(init_db.py)       (models/)         (repositories/)   (routes/ + templates/)
```

| # | Arquivo | O que fazer |
|---|---------|-------------|
| 1 | `server/db/init_db.py` | Criar a tabela no banco |
| 2 | `server/models/ticket.py` | Definir o dataclass |
| 3 | `server/repositories/ticket_repository.py` | Implementar as queries SQL |
| 4 | Rota + template | Usar a entidade numa página |

---

## Passo 1 — Criar a tabela no banco

**Arquivo:** `server/db/init_db.py`

Dentro da função `_create_tables`, adicione o `CREATE TABLE` **após as tabelas que ela referencia** (no exemplo, `users` já existe):

```python
def _create_tables(conn) -> None:
    cursor = conn.cursor()

    # ... tabelas existentes ...

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id          INT             AUTO_INCREMENT PRIMARY KEY,
            user_id     INT             NOT NULL,
            subject     VARCHAR(200)    NOT NULL,
            message     TEXT            NOT NULL,
            status      ENUM('open', 'closed') NOT NULL DEFAULT 'open',
            created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)   # ← adicione aqui

    cursor.close()
    conn.commit()
```

> **Ordem importa:** coloque a `CREATE TABLE` depois das tabelas que ela referencia via `FOREIGN KEY`.
> `tickets` referencia `users`, então vai depois do `CREATE TABLE IF NOT EXISTS users`.

> **`ON UPDATE CURRENT_TIMESTAMP`** atualiza `updated_at` automaticamente sempre que a linha for modificada.

---

## Passo 2 — Definir o modelo Python

**Arquivo:** `server/models/ticket.py` *(arquivo novo)*

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    OPEN   = "open"
    CLOSED = "closed"


@dataclass
class Ticket:
    id:         int
    user_id:    int
    subject:    str
    message:    str
    status:     TicketStatus
    created_at: datetime
    updated_at: datetime
```

### Tipos Python para cada tipo SQL

| SQL | Python |
|-----|--------|
| `INT`, `BIGINT` | `int` |
| `VARCHAR`, `TEXT`, `CHAR` | `str` |
| `DECIMAL`, `FLOAT` | `float` ou `Decimal` |
| `DATE` | `date` (from datetime) |
| `DATETIME`, `TIMESTAMP` | `datetime` (from datetime) |
| `BOOLEAN` | `bool` |
| `ENUM('a','b')` | `str` ou uma `Enum` class |

> Use `ENUM` com uma classe Python quando o campo tiver valores fixos (como `status` aqui).
> Isso previne que um valor inválido seja gravado por engano.

---

## Passo 3 — Criar o repositório

**Arquivo:** `server/repositories/ticket_repository.py` *(arquivo novo)*

```python
from server.models.ticket import Ticket, TicketStatus


def _row_to_ticket(row: dict) -> Ticket:
    return Ticket(
        id=row["id"],
        user_id=row["user_id"],
        subject=row["subject"],
        message=row["message"],
        status=TicketStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TicketRepository:

    @classmethod
    def get_by_id(cls, db, ticket_id: int) -> Ticket | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_ticket(row) if row else None

    @classmethod
    def list_by_user(cls, db, user_id: int) -> list[Ticket]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM tickets WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_ticket(r) for r in rows]

    @classmethod
    def list_all(cls, db) -> list[Ticket]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_ticket(r) for r in rows]

    @classmethod
    def create(cls, db, *, user_id: int, subject: str, message: str) -> Ticket:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tickets (user_id, subject, message)
            VALUES (%s, %s, %s)
            """,
            (user_id, subject.strip(), message.strip()),
        )
        new_id = cursor.lastrowid
        cursor.close()
        return cls.get_by_id(db, new_id)

    @classmethod
    def close(cls, db, ticket_id: int) -> Ticket | None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE tickets SET status = 'closed' WHERE id = %s",
            (ticket_id,),
        )
        cursor.close()
        return cls.get_by_id(db, ticket_id)
```

### Padrões do repositório

**`_row_to_object`** — sempre uma função auxiliar fora da classe que converte um `dict` (retorno do `cursor(dictionary=True)`) em um objeto do modelo. Mantém o código de mapeamento separado.

**`cursor(dictionary=True)`** — necessário apenas no `SELECT`. Faz com que cada linha venha como `{"id": 1, "subject": "..."}` em vez de `(1, "...")`.

**`cursor.lastrowid`** — retorna o `id` gerado pelo `AUTO_INCREMENT` após um `INSERT`.

**Sempre `cursor.close()`** após cada operação — libera o cursor de volta para a conexão.

**`db.commit()`** — **não** é chamado dentro do repositório. É responsabilidade da rota chamar `db.commit()` depois de todas as operações de escrita, ou `db.rollback()` em caso de erro.

---

## Passo 4 — Usar numa rota

**Arquivo:** `server/web/routes/tickets.py` *(arquivo novo)*

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.ticket_repository import TicketRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


@router.get("/tickets")
def tickets_page(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    tickets = TicketRepository.list_by_user(db, user.id)

    return templates.TemplateResponse(
        request=request,
        name="tickets.html",
        context={"request": request, "user": user, "tickets": tickets},
    )


@router.post("/tickets")
async def tickets_submit(
    request: Request,
    subject: str = Form(...),
    message: str = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    form_ctx = {"subject": subject, "message": message}
    error = None

    if len(subject.strip()) < 5:
        error = "Assunto deve ter pelo menos 5 caracteres."
    elif len(message.strip()) < 10:
        error = "Mensagem deve ter pelo menos 10 caracteres."

    if error:
        tickets = TicketRepository.list_by_user(db, user.id)
        return templates.TemplateResponse(
            request=request,
            name="tickets.html",
            context={
                "request": request,
                "user": user,
                "tickets": tickets,
                "error": error,
                "form": form_ctx,
            },
            status_code=422,
        )

    TicketRepository.create(db, user_id=user.id, subject=subject, message=message)
    db.commit()   # ← commit sempre na rota, não no repositório
    return RedirectResponse("/tickets", status_code=302)
```

**Registrar em `server/web/router.py`:**

```python
from server.web.routes.tickets import router as tickets_router

web_router.include_router(tickets_router)
```

---

## Passo 5 — Template

**Arquivo:** `server/templates/tickets.html` *(arquivo novo)*

```jinja
{% extends "dashboard_base.html" %}
{% from "components/forms.html" import input_field %}

{% block title %}Tickets | Banco Digital{% endblock %}

{% block dashboard_content %}
<header class="page-header">
    <h1>Meus Tickets</h1>
</header>

<section class="ui-card">
    <h2>Abrir novo ticket</h2>
    <form method="post" action="/tickets">
        {{ input_field('subject', 'Assunto', value=(form.subject | default(''))) }}
        <label>
            Mensagem
            <textarea name="message">{{ form.message | default('') }}</textarea>
        </label>

        {% if error %}
        <div class="feedback-message mensagem erro feedback-error" style="display: block;">
            {{ error }}
        </div>
        {% endif %}

        <div class="actions">
            <button class="ui-btn ui-btn-primary" type="submit">Enviar</button>
        </div>
    </form>
</section>

<section class="ui-card">
    <h2>Histórico</h2>
    {% for ticket in tickets %}
    <div>
        <strong>{{ ticket.subject }}</strong>
        <span>{{ ticket.status }}</span>
        <p>{{ ticket.message }}</p>
        <small>{{ ticket.created_at.strftime('%d/%m/%Y %H:%M') }}</small>
    </div>
    {% else %}
    <p>Nenhum ticket aberto.</p>
    {% endfor %}
</section>
{% endblock %}
```

---

## Relação muitos-para-muitos (M:N)

Quando duas entidades têm relação M:N (ex.: um usuário tem vários portfólios e um portfólio pertence a vários usuários), usa-se uma tabela intermediária:

```python
# Tabela intermediária: user_portfolios
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_portfolios (
        id           INT    AUTO_INCREMENT PRIMARY KEY,
        portfolio_id INT    NOT NULL,
        user_id      INT    NOT NULL,
        stock_amount DECIMAL(15,4) NOT NULL DEFAULT 0.0000,
        ...
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
        FOREIGN KEY (user_id)      REFERENCES users(id)
    )
""")
```

O repositório da tabela intermediária recebe os dois IDs como parâmetros de busca:

```python
@classmethod
def get_by_user_id(cls, db, user_id: int) -> list[UserPortfolio]:
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM user_portfolios WHERE user_id = %s",
        (user_id,)
    )
    ...
```

---

## Checklist

```
[ ] server/db/init_db.py                           → CREATE TABLE em _create_tables()
[ ] server/models/ticket.py                        → dataclass + Enum se necessário
[ ] server/repositories/ticket_repository.py       → _row_to_ticket + TicketRepository
[ ] server/web/routes/tickets.py                   → GET + POST com require_user
[ ] server/web/router.py                           → include_router
[ ] server/templates/tickets.html                  → extends dashboard_base.html
```
