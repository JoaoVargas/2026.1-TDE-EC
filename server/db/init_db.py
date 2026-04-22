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


def _normalize_usuario_tipo_values() -> None:
    inspector = inspect(engine)
    if "usuarios" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE usuarios SET tipo_usuario = 'manager' "
                "WHERE UPPER(tipo_usuario) = 'MANAGER'"
            )
        )
        connection.execute(
            text(
                "UPDATE usuarios SET tipo_usuario = 'client' "
                "WHERE tipo_usuario IS NULL OR UPPER(tipo_usuario) = 'CLIENT'"
            )
        )
        connection.execute(
            text(
                "UPDATE usuarios SET tipo_usuario = 'client' "
                "WHERE LOWER(tipo_usuario) NOT IN ('client', 'manager')"
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


def _ensure_conta_schema_and_data() -> None:
    inspector = inspect(engine)
    if "contas" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE contas SET tipo_conta = 'checking' "
                "WHERE tipo_conta IS NULL OR LOWER(tipo_conta) IN ('corrente', 'checkings')"
            )
        )
        connection.execute(
            text(
                "UPDATE contas SET tipo_conta = 'savings' "
                "WHERE LOWER(tipo_conta) IN ('poupanca')"
            )
        )
        connection.execute(
            text(
                "UPDATE contas SET tipo_conta = 'checking' "
                "WHERE LOWER(tipo_conta) NOT IN ('checking', 'savings')"
            )
        )

        connection.execute(
            text(
                "UPDATE contas SET numero_conta = LPAD(CAST(id AS CHAR), 10, '0') "
                "WHERE numero_conta IS NULL OR numero_conta = '' OR numero_conta REGEXP '[^0-9]'"
            )
        )
        connection.execute(
            text(
                "UPDATE contas SET numero_conta = LPAD(numero_conta, 10, '0') "
                "WHERE numero_conta REGEXP '^[0-9]+$' AND CHAR_LENGTH(numero_conta) < 10"
            )
        )
        connection.execute(
            text(
                "UPDATE contas SET agencia = '0001' "
                "WHERE agencia IS NULL OR agencia = '' OR agencia REGEXP '[^0-9]' "
                "OR CHAR_LENGTH(agencia) <> 4"
            )
        )

        connection.execute(
            text(
                "ALTER TABLE contas MODIFY COLUMN numero_conta VARCHAR(10) NOT NULL"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE contas MODIFY COLUMN agencia VARCHAR(4) NOT NULL DEFAULT '0001'"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE contas MODIFY COLUMN tipo_conta "
                "ENUM('checking', 'savings') NOT NULL DEFAULT 'checking'"
            )
        )


def init_orm() -> None:
    from server.models import orm_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_usuario_tipo_column()
    _normalize_usuario_tipo_values()
    _ensure_audit_columns()
    _ensure_conta_schema_and_data()
    _drop_gastos_table_if_exists()
    _seed_default_users_if_empty()
