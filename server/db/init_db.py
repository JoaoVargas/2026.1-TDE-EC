from datetime import date

from sqlalchemy import inspect, text

from server.core.security import hash_password
from server.db.base import Base
from server.db.session import SessionLocal, engine
from server.models.orm_models import TipoUsuario
from server.repositories.usuario_repository import UsuarioRepository


def _ensure_usuario_tipo_column() -> None:
    inspector = inspect(engine)
    if "usuarios" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("usuarios")}
    if "tipo_usuario" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE usuarios "
                "ADD COLUMN tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'client'"
            )
        )


def _seed_default_users_if_empty() -> None:
    with SessionLocal() as db:
        if not UsuarioRepository.is_empty(db):
            return

        UsuarioRepository.create(
            db,
            nome="Gerente Padrao",
            email="gerente@gerente.com",
            senha_hash=hash_password("ASDasd123"),
            data_nascimento=date(1988, 1, 10),
            cpf="39053344705",
            cep="80000000",
            logradouro="Rua Gerente",
            numero="100",
            bairro="Centro",
            cidade="Curitiba",
            estado="PR",
            tipo_usuario=TipoUsuario.MANAGER,
        )
        UsuarioRepository.create(
            db,
            nome="Usuario Padrao",
            email="usuario@usuario.com",
            senha_hash=hash_password("ASDasd123"),
            data_nascimento=date(1995, 5, 20),
            cpf="11144477735",
            cep="80010000",
            logradouro="Rua Cliente",
            numero="200",
            bairro="Batel",
            cidade="Curitiba",
            estado="PR",
            tipo_usuario=TipoUsuario.CLIENT,
        )
        db.commit()


def _ensure_audit_columns() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    target_tables = {"usuarios", "contas", "transacoes", "investimentos"}

    with engine.begin() as connection:
        for table_name in sorted(target_tables.intersection(existing_tables)):
            columns = {column["name"] for column in inspector.get_columns(table_name)}

            if "created_at" not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    )
                )

            if "updated_at" not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        "ADD COLUMN updated_at DATETIME NOT NULL "
                        "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                    )
                )


def _drop_gastos_table_if_exists() -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS gastos"))


def init_orm() -> None:
    from server.models import orm_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_usuario_tipo_column()
    _ensure_audit_columns()
    _drop_gastos_table_if_exists()
    _seed_default_users_if_empty()
