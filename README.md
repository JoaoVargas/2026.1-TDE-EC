Inicialize o venv

  python -m venv .venv

  source .venv/bin/activate
  source .venv/bin/activate.fish
  source .venv/Scripts/activate

Se tem o docker instalado então só rodar docker compose up na pasta docker. Se não então instalar e configurar o MySQL na máquina

ORM (SQLAlchemy)

1. Instale as dependências do servidor:

  cd server
  pip install -r requirements.txt

2. A conexão usa as variáveis de ambiente abaixo (ou DB_URL):

  DB_HOST
  DB_PORT
  DB_USER
  DB_PASSWORD
  DB_NAME

3. O setup ORM fica em server/config/db.py:

  engine: conexão com MySQL
  SessionLocal: sessão do banco
  Base: base declarativa dos modelos
  get_db(): dependência para rotas FastAPI

4. Os modelos das tabelas do INIT.sql estão em:

  server/models/orm_models.py