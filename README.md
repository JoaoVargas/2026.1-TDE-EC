# BetaBank — Banco Digital

Aplicação web de banco digital desenvolvida como TDE da disciplina Experiência Criativa (PUCPR 2026.1).

## Tecnologias

- **Python 3.14** + **FastAPI** — servidor ASGI com renderização server-side (SSR)
- **Jinja2** — templates HTML
- **MySQL 8.4** — banco de dados relacional
- **mysql-connector-python** — driver de conexão com pool nativo
- **bcrypt** — hash de senhas
- **Docker Compose** — infraestrutura local (MySQL + servidor + Portainer)
- **Vanilla JS / CSS** — frontend sem frameworks, organizado em componentes

## Arquitetura

O projeto segue uma arquitetura **SSR pura**: não há rotas de API; todos os dados são buscados diretamente nas rotas web e injetados nos templates Jinja2. O JavaScript do cliente é restrito a interações de UI.

```
server/
├── main.py                  # entrypoint ASGI
├── core/
│   ├── app.py               # factory da aplicação, middlewares, montagem de routers
│   ├── settings.py          # configurações lidas de variáveis de ambiente
│   ├── session.py           # helpers de sessão (cookie session_id)
│   └── security.py          # hash/verificação de senha
├── db/
│   ├── connection.py        # pool de conexões MySQL e health check
│   └── init_db.py           # criação das tabelas no startup
├── models/                  # dataclasses das entidades de domínio
│   ├── user.py              # User, UserType (client | manager)
│   ├── address.py
│   ├── account.py
│   ├── transaction.py
│   ├── portfolio.py
│   ├── manager_portfolio.py
│   ├── user_portfolio.py
│   └── user_avatar.py
├── repositories/            # acesso a dados (SQL puro via connection pool)
│   ├── user_repository.py
│   ├── address_repository.py
│   ├── account_repository.py
│   ├── transaction_repository.py
│   ├── portfolio_repository.py
│   ├── manager_portfolio_repository.py
│   ├── user_portfolio_repository.py
│   ├── user_avatar_repository.py
│   └── session_repository.py
├── web/
│   ├── router.py            # agrega todos os sub-routers
│   └── routes/              # uma rota por página
│       ├── login.py / logout.py / cadastro.py
│       ├── home.py
│       ├── operacao.py
│       ├── extrato.py
│       ├── investimentos.py
│       ├── perfil.py
│       ├── manager.py
│       ├── manager_accounts.py
│       └── manager_select.py
├── templates/               # templates Jinja2
│   ├── base.html / auth_base.html / dashboard_base.html
│   ├── components/          # macros e partials reutilizáveis
│   └── *.html               # uma template por página
└── static/
    ├── css/                 # folhas de estilo por página + tokens de design
    └── js/
        ├── components/      # módulos JS reutilizáveis
        │   ├── cep-lookup.js
        │   ├── date-range-picker.js
        │   ├── modal.js
        │   ├── sidebar.js
        │   ├── transaction-flow.js
        │   ├── form-feedback.js
        │   ├── formatters.js
        │   └── ui-cards.js
        └── pages/           # JS específico por página
```

### Autenticação e sessões

As sessões são armazenadas na tabela `sessions` do banco de dados. No login, um token opaco é gerado e salvo no cookie `session_id` (HttpOnly, SameSite=Lax). O `SessionRefreshMiddleware` renova automaticamente a expiração a cada requisição autenticada.

Variáveis relevantes: `SESSION_SECRET`, `SESSION_TIMEOUT_SECONDS` (padrão: 300 s).

### Tipos de usuário

| Tipo | Acesso |
|------|--------|
| `client` | Dashboard, extrato, operações, investimentos, perfil |
| `manager` | Painel de gestão, visualização de contas de clientes |

## Configuração

Copie o arquivo de exemplo e ajuste as variáveis:

```bash
cp docker/.env.example docker/.env   # se existir; caso contrário crie docker/.env
```

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_HOST` | `localhost` | Host do MySQL |
| `DB_PORT` | `3306` | Porta do MySQL |
| `DB_USER` | `user` | Usuário do banco |
| `DB_PASSWORD` | `password` | Senha do banco |
| `DB_NAME` | `bancodigital` | Nome do banco |
| `DB_URL` | — | URL completa (substitui os campos acima) |
| `SESSION_SECRET` | `change-me-in-production` | Segredo das sessões |
| `SESSION_TIMEOUT_SECONDS` | `300` | Duração da sessão em segundos |
| `APP_NAME` | `Banco Digital` | Nome exibido na aplicação |
| `DEBUG` | `false` | Modo debug do FastAPI |
| `DB_ECHO` | `false` | Log das queries SQL |
| `DB_POOL_SIZE` | `5` | Tamanho do pool de conexões |
| `DB_MAX_OVERFLOW` | `10` | Conexões extras além do pool |
| `DB_POOL_TIMEOUT` | `30` | Timeout de aquisição de conexão (s) |
| `DB_POOL_RECYCLE` | `3600` | Reciclagem de conexões (s) |

## Subindo com Docker (recomendado)

```bash
cd docker
docker compose up
```

Serviços disponíveis:

| Serviço | Porta padrão | Descrição |
|---------|-------------|-----------|
| `betabank-db` | `3000` | MySQL 8.4 |
| `betabank-server` | `3001` | Aplicação FastAPI |
| `betabank-portainer` | `3002` | Painel de gerenciamento Docker |

## Executando localmente

```bash
# 1. Crie e ative o ambiente virtual
cd server
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
source .venv/Scripts/activate    # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente (ou crie um .env na raiz)
export DB_HOST=localhost DB_USER=user DB_PASSWORD=password DB_NAME=bancodigital

# 4. Execute o servidor
cd ..
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

A aplicação inicializa o banco automaticamente no startup (`init_db`).

## Páginas

| Rota | Descrição |
|------|-----------|
| `/login` | Login |
| `/cadastro` | Cadastro de novo cliente (com busca automática de endereço por CEP) |
| `/home` | Dashboard do cliente |
| `/operacao` | Depósito, saque e transferência |
| `/extrato` | Histórico de transações com filtro por período |
| `/investimentos` | Carteira de investimentos e distribuição |
| `/perfil` | Dados pessoais e avatar |
| `/manager` | Painel do gestor |
| `/manager/select` | Seleção de cliente para gestão |
| `/manager/accounts` | Contas do cliente selecionado |
