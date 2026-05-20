# Tutorial: Adicionando uma nova operação financeira

> Exemplo usado: operação de **pagamento de boleto** (`boleto`).
> O cliente informa o valor e uma descrição, o dinheiro sai da conta corrente.

---

## Como as operações financeiras funcionam

Toda movimentação de dinheiro no sistema é um **`Transaction`** na tabela `transactions`:

```sql
transactions (
    id              INT,
    type            ENUM('internal','transaction','expense','other','deposit','withdrawal'),
    from_account_id INT,   -- conta de origem (NULL em depósitos)
    to_account_id   INT,   -- conta de destino (NULL em saques/despesas)
    amount          DECIMAL(15,2),
    description     VARCHAR(255)
)
```

O campo `type` é um `ENUM` — para adicionar um novo tipo de operação, você precisa primeiro expandir esse enum.

---

## Visão geral das mudanças

| # | Arquivo | O que fazer |
|---|---------|-------------|
| 1 | `server/db/init_db.py` | Expandir o ENUM `type` na tabela |
| 2 | `server/models/transaction.py` | Adicionar o novo valor ao `TransactionType` |
| 3 | `server/web/routes/operacao.py` | Tratar o novo modo no endpoint existente |
| 4 | `server/templates/operacao.html` | Mostrar o formulário do novo modo |
| 5 | `server/static/js/pages/operacao.js` | *(opcional)* Lógica de UI do novo modo |

---

## Passo 1 — Expandir o ENUM no banco

**Arquivo:** `server/db/init_db.py`

O `CREATE TABLE` já define o ENUM inicial. Para bancos que já existem, use `_apply_migrations` para alterar o tipo da coluna com o novo valor incluído:

```python
def _apply_migrations(conn) -> None:
    cursor = conn.cursor()

    # ... migrações existentes ...

    if not _enum_has_value(cursor, "transactions", "type", "boleto"):  # ← adicione
        cursor.execute(
            "ALTER TABLE transactions MODIFY COLUMN type "
            "ENUM('internal','transaction','expense','other','deposit','withdrawal','boleto') NOT NULL"
        )
        conn.commit()

    cursor.close()
```

E atualize também o `CREATE TABLE IF NOT EXISTS transactions` (para novos ambientes):

```python
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        ...
        type ENUM('internal','transaction','expense','other','deposit','withdrawal','boleto') NOT NULL,
        ...
    )
""")
```

> **`_enum_has_value`** verifica no `INFORMATION_SCHEMA` se o valor já está no ENUM — assim a migração é segura de rodar mais de uma vez.

---

## Passo 2 — Atualizar o modelo Python

**Arquivo:** `server/models/transaction.py`

Adicione o novo valor ao `TransactionType`:

```python
class TransactionType(str, Enum):
    INTERNAL    = "internal"
    TRANSACTION = "transaction"
    EXPENSE     = "expense"
    OTHER       = "other"
    DEPOSIT     = "deposit"
    WITHDRAWAL  = "withdrawal"
    BOLETO      = "boleto"    # ← adicione aqui
```

> O valor da string (`"boleto"`) deve ser **exatamente igual** ao valor no ENUM do banco.

---

## Passo 3 — Tratar o novo modo na rota

**Arquivo:** `server/web/routes/operacao.py`

A rota de operações aceita um parâmetro `?modo=` na URL. Você precisa tratar o novo modo tanto no `GET` quanto no `POST`.

### No `GET` (exibir formulário):

```python
@router.get("/operacao")
def operacao_page(request: Request, modo: str = "depositar", db=Depends(get_db)):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    modos_validos = {"depositar", "sacar", "transferir", "boleto"}  # ← adicione "boleto"
    if modo not in modos_validos:
        return RedirectResponse("/operacao?modo=depositar", status_code=302)

    checking_account = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)

    return templates.TemplateResponse(
        request=request,
        name="operacao.html",
        context={
            "request": request,
            "user": user,
            "modo": modo,
            "checking_account": checking_account,
        },
    )
```

### No `POST` (processar operação):

```python
@router.post("/operacao")
async def operacao_submit(
    request: Request,
    modo: str = Form(...),
    valor: str = Form(...),
    descricao: str = Form(""),
    db=Depends(get_db),
):
    result = require_user(request, db)
    if isinstance(result, RedirectResponse):
        return result
    user = result

    # Converte o valor (cents → reais, ex: "1050" → Decimal("10.50"))
    try:
        amount = Decimal(valor) / 100
    except Exception:
        amount = Decimal("0")

    error = None
    checking = AccountRepository.get_by_user_and_type(db, user.id, AccountType.CHECKING)

    if modo == "boleto":
        if amount <= 0:
            error = "Valor inválido."
        elif checking.balance < amount:
            error = "Saldo insuficiente."
        else:
            # Cria a transação: dinheiro SAI da conta corrente (from=checking, to=None)
            TransactionRepository.create(
                db,
                type=TransactionType.BOLETO,
                from_account_id=checking.id,
                to_account_id=None,
                amount=amount,
                description=descricao.strip() or "Pagamento de boleto",
            )
            # Atualiza o saldo
            AccountRepository.debit(db, account_id=checking.id, amount=amount)
            db.commit()
            return RedirectResponse("/home?flash=boleto_pago", status_code=302)

    # ... outros modos (depositar, sacar, transferir) ...

    if error:
        return templates.TemplateResponse(
            request=request,
            name="operacao.html",
            context={
                "request": request,
                "user": user,
                "modo": modo,
                "error": error,
                "checking_account": checking,
            },
            status_code=422,
        )
```

### Referência: como cada tipo de transação usa `from`/`to`

| Operação | `from_account_id` | `to_account_id` | Saldo afetado |
|----------|-------------------|-----------------|---------------|
| Depósito | `None` | conta do usuário | + conta destino |
| Saque | conta do usuário | `None` | - conta origem |
| Transferência | conta de origem | conta de destino | - origem, + destino |
| Boleto | conta corrente | `None` | - conta origem |

---

## Passo 4 — Atualizar o template

**Arquivo:** `server/templates/operacao.html`

Adicione o formulário do novo modo dentro do bloco de conteúdo, usando condicionais Jinja:

```jinja
{% if modo == 'boleto' %}
<section class="ui-card operacao-form">
    <h2>Pagar Boleto</h2>
    <form method="post" action="/operacao" id="form-boleto">
        <input type="hidden" name="modo" value="boleto" />

        <div class="form-group">
            <label>Valor</label>
            <input
                type="text"
                name="valor"
                id="valor-boleto"
                inputmode="numeric"
                placeholder="R$ 0,00"
                required
            />
        </div>

        <div class="form-group">
            <label>Descrição (opcional)</label>
            <input type="text" name="descricao" maxlength="200" />
        </div>

        {% if error and modo == 'boleto' %}
        <div class="feedback-message mensagem erro feedback-error" style="display: block;">
            {{ error }}
        </div>
        {% endif %}

        <div class="actions">
            <button class="ui-btn ui-btn-primary" type="submit">Pagar</button>
        </div>
    </form>
</section>
{% endif %}
```

Adicione também o link de navegação para o novo modo no menu de operações:

```jinja
<nav class="operacao-tabs">
    <a href="/operacao?modo=depositar" class="{{ 'active' if modo == 'depositar' }}">Depositar</a>
    <a href="/operacao?modo=sacar"     class="{{ 'active' if modo == 'sacar' }}">Sacar</a>
    <a href="/operacao?modo=transferir" class="{{ 'active' if modo == 'transferir' }}">Transferir</a>
    <a href="/operacao?modo=boleto"    class="{{ 'active' if modo == 'boleto' }}">Boleto</a>
</nav>
```

---

## Passo 5 *(opcional)* — Lógica de UI no JavaScript

**Arquivo:** `server/static/js/pages/operacao.js`

O JS da página de operações gerencia qual formulário mostrar e formata o input de valor. Adicione o novo modo ao mapa de formulários:

```javascript
const formIds = {
    depositar:  "form-depositar",
    sacar:      "form-sacar",
    transferir: "form-transferir",
    boleto:     "form-boleto",    // ← adicione aqui
};

// O campo de valor do boleto também precisa de máscara de moeda
const valorBoleto = document.getElementById("valor-boleto");
if (valorBoleto) {
    valorBoleto.addEventListener("input", formatarComoMoeda);
}
```

---

## Exibindo a nova operação no extrato

O extrato (`/extrato`) lista todas as transações de uma conta. Por usar `SELECT * FROM transactions WHERE account_id = ?`, ele **já vai mostrar** as transações de boleto automaticamente — sem nenhuma alteração.

Se quiser um rótulo diferente para o novo tipo no extrato:

**Arquivo:** `server/templates/extrato.html`

```jinja
{% set tipo_label = {
    'deposit':     'Depósito',
    'withdrawal':  'Saque',
    'transaction': 'Transferência',
    'boleto':      'Pagamento de Boleto',   {# ← adicione aqui #}
} %}

<td>{{ tipo_label.get(t.type, t.type) }}</td>
```

---

## Checklist

```
[ ] server/db/init_db.py
      → CREATE TABLE: adicionar valor ao ENUM
      → _apply_migrations(): ALTER TABLE MODIFY COLUMN com _enum_has_value

[ ] server/models/transaction.py
      → adicionar TransactionType.BOLETO = "boleto"

[ ] server/web/routes/operacao.py
      → GET: adicionar "boleto" ao set de modos válidos
      → POST: bloco if modo == "boleto" com validação + criação da transação

[ ] server/templates/operacao.html
      → bloco {% if modo == 'boleto' %} com o formulário
      → link de navegação no menu de tabs

[ ] (opcional) server/static/js/pages/operacao.js
      → novo formId no mapa + máscara de valor se necessário

[ ] (opcional) server/templates/extrato.html
      → rótulo amigável para o novo tipo
```
