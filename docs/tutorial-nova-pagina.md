# Tutorial: Adicionando uma nova página ao sistema

> Exemplo usado: página `/extrato-anual` que exibe um resumo anual de transações do usuário.

---

## Visão geral

Toda página no sistema segue o mesmo padrão de 3 arquivos:

| # | Arquivo | O que fazer |
|---|---------|-------------|
| 1 | `server/web/routes/minha_pagina.py` | Lógica: busca dados e responde à requisição |
| 2 | `server/web/router.py` | Registrar a rota no app |
| 3 | `server/templates/minha_pagina.html` | Visual: o HTML da página |
| 4 | `server/static/js/pages/minha_pagina.js` | *(opcional)* Interatividade no browser |

---

## Passo 1 — Criar o arquivo de rota

**Arquivo:** `server/web/routes/extrato_anual.py` *(arquivo novo)*

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from server.db.connection import get_db
from server.repositories.transaction_repository import TransactionRepository
from server.web.routes._shared import require_user, templates

router = APIRouter(tags=["pages"])


@router.get("/extrato-anual")
def extrato_anual_page(request: Request, db=Depends(get_db)):
    # 1. Verifica se o usuário está logado
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    # 2. Busca os dados necessários
    transacoes = TransactionRepository.get_by_account_id(db, account_id=...)

    # 3. Renderiza o template com os dados
    return templates.TemplateResponse(
        request=request,
        name="extrato_anual.html",
        context={
            "request": request,
            "user": user,
            "transacoes": transacoes,
        },
    )
```

> **`require_user`** faz a guarda de autenticação.
> Se o usuário não estiver logado, retorna um `RedirectResponse` para `/login`.
> O padrão `if isinstance(result, RedirectResponse): return result` é obrigatório logo depois.

---

## Passo 2 — Registrar a rota no app

**Arquivo:** `server/web/router.py`

Adicione o import e o `include_router`:

```python
from server.web.routes.extrato_anual import router as extrato_anual_router  # ← novo import

# ... outros imports ...

web_router = APIRouter()
web_router.include_router(extrato_anual_router)   # ← registrar
# ... outros include_router ...
```

> Sem isso a rota simplesmente não existirá — o FastAPI não descobre rotas automaticamente.

---

## Passo 3 — Criar o template HTML

**Arquivo:** `server/templates/extrato_anual.html` *(arquivo novo)*

```jinja
{% extends "dashboard_base.html" %}

{% block title %}Extrato Anual | Banco Digital{% endblock %}

{% block dashboard_styles %}
<link rel="stylesheet" href="/static/css/extrato_anual.css" />
{% endblock %}

{% block dashboard_content %}
<header class="page-header">
    <h1>Extrato Anual</h1>
</header>

{% if transacoes %}
<section class="ui-card">
    <table>
        <thead>
            <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Valor</th>
            </tr>
        </thead>
        <tbody>
            {% for t in transacoes %}
            <tr>
                <td>{{ t.created_at.strftime('%d/%m/%Y') }}</td>
                <td>{{ t.description or '—' }}</td>
                <td>{{ t.amount | brl }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</section>
{% else %}
<p>Nenhuma transação encontrada.</p>
{% endif %}
{% endblock %}

{% block dashboard_scripts %}
<script type="module" src="/static/js/pages/extrato_anual.js"></script>
{% endblock %}
```

### Estrutura de herança dos templates

```
base.html
├── auth_base.html          → páginas de login e cadastro
└── dashboard_base.html     → todas as páginas internas (após login)
```

**Sempre use `dashboard_base.html`** para páginas que exigem login.
O sidebar, topbar e menu já são incluídos automaticamente.

### Blocos disponíveis no `dashboard_base.html`

| Bloco | Para que serve |
|-------|----------------|
| `title` | Título da aba do browser |
| `dashboard_styles` | `<link>` de CSS específico da página |
| `dashboard_content` | Conteúdo principal da página |
| `dashboard_scripts` | `<script>` de JS específico da página |

---

## Passo 4 *(opcional)* — Criar o arquivo JavaScript

**Arquivo:** `server/static/js/pages/extrato_anual.js` *(arquivo novo)*

```javascript
// Lógica específica desta página (filtros, animações, etc.)
document.addEventListener("DOMContentLoaded", () => {
    console.log("Extrato anual carregado");
});
```

O arquivo é carregado via `<script type="module">` no bloco `dashboard_scripts` do template.

---

## Variações comuns

### Página com formulário (GET mostra, POST processa)

```python
@router.get("/minha-pagina")
def minha_pagina_get(request: Request, db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    return templates.TemplateResponse(
        request=request,
        name="minha_pagina.html",
        context={"request": request, "user": user, "form": {}},
    )


@router.post("/minha-pagina")
async def minha_pagina_post(
    request: Request,
    campo: str = Form(...),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    form_ctx = {"campo": campo}

    # Validação
    if not campo.strip():
        return templates.TemplateResponse(
            request=request,
            name="minha_pagina.html",
            context={"request": request, "user": user, "error": "Campo obrigatório.", "form": form_ctx},
            status_code=422,
        )

    # Processamento
    db.commit()
    return RedirectResponse("/home", status_code=302)
```

### Página exclusiva para gerentes

Troque `require_user` por `require_manager`:

```python
from server.web.routes._shared import require_manager

result = require_manager(request, db)
if isinstance(result, RedirectResponse):
    return result
user = result
```

Se um cliente tentar acessar, será redirecionado para `/home`.

### Parâmetro na URL

```python
@router.get("/usuario/{user_id}")
def detalhe_usuario(request: Request, user_id: int, db=Depends(get_db)):
    result = require_manager(request, db)
    if isinstance(result, RedirectResponse):
        return result

    usuario = UserRepository.get_by_id(db, user_id)
    if not usuario:
        return RedirectResponse("/manager", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="detalhe_usuario.html",
        context={"request": request, "user": result, "usuario": usuario},
    )
```

### Query string (filtros)

```python
@router.get("/extrato")
def extrato_page(request: Request, account: str = "corrente", db=Depends(get_db)):
    # ?account=corrente ou ?account=poupanca
    ...
```

---

## Exibindo erros e mensagens de sucesso no template

```jinja
{# Erro de validação #}
{% if error %}
<div class="feedback-message mensagem erro feedback-error" style="display: block;">
    {{ error }}
</div>
{% endif %}

{# Mensagem de sucesso (passada via query string ou context) #}
{% if flash == 'salvo' %}
<div class="feedback-message mensagem sucesso feedback-success" style="display: block;">
    Dados salvos com sucesso!
</div>
{% endif %}
```

---

## Checklist

```
[ ] server/web/routes/minha_pagina.py    → criado com router + @router.get/@router.post
[ ] server/web/router.py                 → import + include_router adicionados
[ ] server/templates/minha_pagina.html  → extends dashboard_base.html
[ ] (opcional) server/static/js/pages/  → arquivo .js se tiver interatividade
```
