Setup do ambiente

1. Crie e ative um ambiente virtual:

  python -m venv .venv

  source .venv/bin/activate
  source .venv/bin/activate.fish
  source .venv/Scripts/activate

2. Instale as dependencias do servidor:

  cd server
  pip install -r requirements.txt

3. Suba a infraestrutura com Docker (opcional, recomendado):

  cd ../docker
  docker compose up

Configuracao

A conexao com banco usa DB_URL ou os campos abaixo:

- DB_HOST
- DB_PORT
- DB_USER
- DB_PASSWORD
- DB_NAME

Opcoes de tuning do SQLAlchemy (opcionais):

- DB_ECHO (true/false)
- DB_POOL_SIZE
- DB_MAX_OVERFLOW
- DB_POOL_TIMEOUT
- DB_POOL_RECYCLE

Configuracoes adicionais da API:

- APP_NAME
- DEBUG
- CORS_ALLOW_ORIGINS (lista separada por virgula)

Arquitetura do servidor

- server/main.py: entrypoint ASGI (apenas cria a aplicacao)
- server/core/settings.py: leitura e cache de configuracoes
- server/core/app.py: factory da aplicacao FastAPI, middlewares e routers
- server/web/router.py: roteador para paginas HTML
- server/web/routes/pages.py: rotas web renderizadas com Jinja2
- server/templates/: templates Jinja2
- server/static/: arquivos estaticos (CSS, imagens, etc.)
- server/db/base.py: Base declarativa do SQLAlchemy
- server/db/session.py: engine, SessionLocal e check de conectividade
- server/db/init_db.py: inicializacao das tabelas
- server/models/orm_models.py: entidades ORM
- server/repositories/table_repository.py: acesso a dados
- server/api/routes/: endpoints HTTP

Compatibilidade

O modulo server/models/example.py continua funcionando como camada de compatibilidade para imports legados.

Executando a API

Na raiz do projeto:

  uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

Health check:

  GET /api/health

Paginas HTML:

  GET /
  GET /healthcheck