# Documentação do projeto

---

## Documentação disponível

| Arquivo | Quando usar |
|---------|-------------|
| [arquitetura.md](arquitetura.md) | Entender como o projeto funciona por dentro — stack, camadas, fluxo de uma requisição |
| [tutorial-nova-coluna-usuario.md](tutorial-nova-coluna-usuario.md) | Adicionar um campo novo no cadastro de usuário (ex: telefone, score) |
| [tutorial-nova-pagina.md](tutorial-nova-pagina.md) | Criar uma nova página no sistema (rota + template + JS) |
| [tutorial-nova-entidade.md](tutorial-nova-entidade.md) | Criar uma nova entidade do zero (tabela + modelo + repositório) |
| [tutorial-nova-operacao-financeira.md](tutorial-nova-operacao-financeira.md) | Adicionar um novo tipo de transação (ex: boleto, pix) |
| [tutorial-autenticacao-sessoes.md](tutorial-autenticacao-sessoes.md) | Entender o sistema de login/logout e como proteger rotas |

---

## Onde cada coisa fica

```
server/
├── main.py                     ponto de entrada (expõe `app` para o uvicorn)
├── core/
│   ├── app.py                  monta o FastAPI: middlewares, lifespan, rotas
│   ├── settings.py             lê variáveis do .env
│   ├── session.py              leitura/gravação do cookie de sessão
│   └── security.py             hash_password(), verify_password()
├── db/
│   ├── connection.py           pool MySQL + get_db()
│   └── init_db.py              CREATE TABLE, migrações, seed inicial
├── models/                     dataclasses — forma dos dados (User, Account, ...)
├── repositories/               queries SQL (UserRepository, AccountRepository, ...)
├── web/
│   ├── router.py               agrega todos os routers
│   └── routes/
│       ├── _shared.py          require_user(), require_manager(), filtros Jinja
│       └── *.py                uma rota por página
├── templates/                  HTML Jinja2
│   ├── base.html               layout raiz
│   ├── auth_base.html          layout login/cadastro
│   ├── dashboard_base.html     layout painel interno
│   └── components/             macros reutilizáveis
└── static/
    ├── css/
    └── js/
        ├── components/         módulos JS reutilizáveis
        └── pages/              JS específico de cada página
```

---

## Ferramenta de linha de comando

Para adicionar uma coluna nova no cadastro de usuário de forma automática:

```bash
# Na raiz do projeto
python add_column.py <tabela> <coluna> <tipo_sql> [--label "Texto"] [--not-null]

# Exemplos
python add_column.py users phone VARCHAR(20) --label "Telefone"
python add_column.py users score INT --not-null
python add_column.py users birth_date DATE --label "Data extra"
```

O script edita automaticamente os 6 arquivos descritos em `tutorial-nova-coluna-usuario.md`.
