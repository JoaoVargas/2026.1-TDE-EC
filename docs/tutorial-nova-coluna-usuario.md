# Tutorial: Adicionando uma nova coluna no cadastro de usuário

> Exemplo usado ao longo do tutorial: coluna `phone` (telefone), tipo `VARCHAR(20)`, opcional (pode ser nulo).

---

## Visão geral

Ao adicionar uma coluna no banco, você precisa atualizar **6 lugares** para que tudo funcione de ponta a ponta:

| # | Arquivo | O que fazer |
|---|---------|-------------|
| 1 | `server/db/init_db.py` | Declarar a coluna no banco |
| 2 | `server/models/user.py` | Declarar o campo no modelo Python |
| 3 | `server/repositories/user_repository.py` | Ler e gravar a coluna |
| 4 | `server/web/routes/cadastro.py` | Receber o campo no formulário |
| 5 | `server/templates/cadastro.html` | Mostrar o input na tela |
| 6 | `server/templates/home.html` | *(opcional)* Exibir o valor na home |

---

## Passo 1 — Declarar a coluna no banco

**Arquivo:** `server/db/init_db.py`

Há dois lugares a alterar aqui.

### 1a. No `CREATE TABLE` da tabela `users`

Para bancos criados do zero, adicione a linha da nova coluna **antes de `created_at`**:

```python
CREATE TABLE IF NOT EXISTS users (
    id           INT           AUTO_INCREMENT PRIMARY KEY,
    ...
    birthday     DATE          NOT NULL,
    address_id   INT           NOT NULL,
    phone        VARCHAR(20),          # ← adicione aqui
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ...
)
```

### 1b. Na função `_apply_migrations`

Para bancos que já existem, adicione um bloco de migração **antes de `cursor.close()`**.
O `_column_exists` garante que o `ALTER TABLE` só roda uma vez:

```python
def _apply_migrations(conn) -> None:
    cursor = conn.cursor()

    # ... migrações existentes ...

    if not _column_exists(cursor, "users", "phone"):   # ← adicione aqui
        cursor.execute(
            "ALTER TABLE users ADD COLUMN phone VARCHAR(20)"
        )
        conn.commit()

    cursor.close()
```

> **Por que dois lugares?**
> O `CREATE TABLE` cria a tabela correta para novos ambientes.
> O `ALTER TABLE` atualiza bancos que já estão rodando sem precisar recriar tudo.

---

## Passo 2 — Declarar o campo no modelo Python

**Arquivo:** `server/models/user.py`

O `User` é um `dataclass` — cada coluna do banco precisa de um atributo correspondente aqui.
Adicione o campo novo **após `address_id`**:

```python
@dataclass
class User:
    id: int
    cpf: str
    type: UserType
    name: str
    email: str
    password: str
    birthday: date
    address_id: int
    phone: str | None   # ← adicione aqui
    created_at: datetime
    updated_at: datetime
    has_avatar: bool = False
```

> **`str | None`** significa que o campo aceita texto **ou** `None` (quando o usuário não preencheu).

---

## Passo 3 — Ler e gravar a coluna no repositório

**Arquivo:** `server/repositories/user_repository.py`

### 3a. `_row_to_user` — mapear a linha do banco para o objeto `User`

Essa função transforma o resultado do `SELECT * FROM users` em um objeto `User`.
Adicione o campo **após `address_id`**:

```python
def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        ...
        address_id=row["address_id"],
        phone=row["phone"],          # ← adicione aqui
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
```

### 3b. `create()` — parâmetro na assinatura

Adicione o parâmetro novo **antes de `create_default_account`**:

```python
@classmethod
def create(
    cls,
    db,
    *,
    cpf: str,
    ...
    address_id: int,
    phone: str | None,               # ← adicione aqui
    create_default_account: bool = True,
) -> User:
```

### 3c. `create()` — incluir na query `INSERT`

Há três partes da query para atualizar:

```python
cursor.execute(
    """
    INSERT INTO users (cpf, type, name, email, password, birthday, phone, address_id)
    --                                                              ↑ 1. coluna aqui
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    --                              ↑ 2. mais um %s aqui
    """,
    (
        cls._normalize_cpf(cpf),
        type.value,
        name.strip(),
        cls._normalize_email(email),
        password_hash,
        birthday,
        phone,          # ← 3. valor aqui (mesma posição da coluna acima)
        address_id,
    ),
)
```

> **Atenção à ordem:** o valor de `phone` na tupla deve estar na **mesma posição** que o nome `phone` na lista de colunas do `INSERT`.

---

## Passo 4 — Receber o campo no formulário

**Arquivo:** `server/web/routes/cadastro.py`

### 4a. Parâmetro do endpoint `cadastro_submit`

O FastAPI lê o formulário HTML automaticamente pelo nome do parâmetro.
Adicione **antes de `db=Depends`**:

```python
@router.post("/cadastro")
async def cadastro_submit(
    request: Request,
    nome: str = Form(...),
    ...
    estado: str = Form(...),
    phone: str | None = Form(None),  # ← adicione aqui
    db=Depends(get_db),
):
```

> **`Form(None)`** define o valor padrão como `None` — o campo é **opcional**.
> Se o usuário não preencher, não causa erro de validação.

### 4b. Adicionar ao `form_ctx`

O `form_ctx` repopula o formulário quando há erro de validação, para o usuário não precisar redigitar tudo. Adicione o campo:

```python
form_ctx = {
    "nome": nome, "email": email, "cpf": cpf, "nascimento": nascimento,
    "cep": cep, "logradouro": logradouro, "numero": numero,
    "bairro": bairro, "cidade": cidade, "estado": estado,
    "phone": phone,   # ← adicione aqui
}
```

### 4c. Passar para `UserRepository.create()`

Na chamada de criação do usuário, passe o valor recebido:

```python
user = UserRepository.create(
    db,
    cpf=cpf_digits,
    name=name_norm,
    email=email_norm,
    password_hash=hash_password(senha),
    birthday=date.fromisoformat(nascimento),
    address_id=address.id,
    phone=phone,   # ← adicione aqui
)
```

---

## Passo 5 — Adicionar o input no formulário HTML

**Arquivo:** `server/templates/cadastro.html`

Use a macro `input_field` que já existe no projeto. Adicione o input no lugar que fizer sentido visualmente — por exemplo, após `nascimento` e antes de `senha`:

```jinja
{{ input_field('nascimento', 'Data de nascimento', 'date', value=(form.nascimento | default(''))) }}
{{ input_field('phone', 'Telefone', value=(form.phone | default(''))) }}
{{ input_field('senha', 'Senha', 'password', 'new-password') }}
```

> O primeiro argumento do `input_field` deve ser **exatamente igual** ao nome do parâmetro no endpoint (`phone`).
> É assim que o HTML conecta com o Python.

A macro aceita os seguintes argumentos, em ordem:

```
input_field(name, label, type='text', autocomplete='', class='', value='')
```

Exemplos de uso para outros tipos de campo:

```jinja
{# Campo de texto simples (padrão) #}
{{ input_field('phone', 'Telefone', value=(form.phone | default(''))) }}

{# Campo numérico #}
{{ input_field('score', 'Pontuação', 'number', value=(form.score | default(''))) }}

{# Campo de data #}
{{ input_field('birth_date', 'Data', 'date', value=(form.birth_date | default(''))) }}
```

---

## Passo 6 *(opcional)* — Exibir na home

**Arquivo:** `server/templates/home.html`

Se quiser mostrar o campo na página inicial do usuário após o login:

```jinja
<header class="greeting-block">
    <h1>Ola, {{ user.name if user else 'Usuario' }}</h1>
    <p>Resumo rapido da sua conta e atalhos do BetaBank.</p>
    <p><strong>Telefone:</strong> {{ user.phone if user else '' }}</p>
</header>
```

---

## Resumo final

```
server/db/init_db.py
  └─ CREATE TABLE users        → adicionar coluna antes de created_at
  └─ _apply_migrations()       → adicionar bloco ALTER TABLE com _column_exists

server/models/user.py
  └─ class User                → adicionar atributo após address_id

server/repositories/user_repository.py
  └─ _row_to_user()            → mapear row["phone"] → User.phone
  └─ create() assinatura       → adicionar parâmetro antes de create_default_account
  └─ create() INSERT           → coluna, %s e valor na tupla

server/web/routes/cadastro.py
  └─ cadastro_submit()         → parâmetro Form antes de db=Depends
  └─ form_ctx                  → adicionar chave ao dicionário
  └─ UserRepository.create()   → passar o kwarg

server/templates/cadastro.html → input_field com o nome do campo
server/templates/home.html     → exibição (opcional)
```

---

## IMPORTANTE!

Depois de salvar tudo, **reinicie o servidor** — a função `_apply_migrations` vai rodar automaticamente e adicionar a coluna no banco.

---

> **Dica:** Se quiser automatizar esse processo, o script `add_column.py` na raiz do projeto faz todas essas alterações de uma vez:
> ```bash
> python add_column.py users phone VARCHAR(20) --label "Telefone"
> ```
