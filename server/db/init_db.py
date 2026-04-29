from datetime import date

import mysql.connector

from server.core.security import hash_password
from server.db.connection import _get_pool
from server.models.usuario import TipoUsuario


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (table_name,),
    )
    return cursor.fetchone()[0] > 0


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table_name, column_name),
    )
    return cursor.fetchone()[0] > 0


def _create_tables(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            senha VARCHAR(255) NOT NULL,
            data_nascimento DATE NOT NULL,
            cpf VARCHAR(14) NOT NULL UNIQUE,
            cep VARCHAR(9) NOT NULL,
            logradouro VARCHAR(200),
            numero VARCHAR(10),
            bairro VARCHAR(100),
            cidade VARCHAR(100),
            estado VARCHAR(2),
            tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'client',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            numero_conta VARCHAR(10) NOT NULL UNIQUE,
            agencia VARCHAR(4) NOT NULL DEFAULT '0001',
            saldo DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
            tipo_conta ENUM('checking', 'savings') NOT NULL DEFAULT 'checking',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conta_id INT NOT NULL,
            tipo_transacao VARCHAR(30) NOT NULL,
            descricao VARCHAR(255),
            valor DECIMAL(15, 2) NOT NULL,
            data_transacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (conta_id) REFERENCES contas(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            tipo_investimento VARCHAR(50) NOT NULL,
            nome_ativo VARCHAR(100) NOT NULL,
            valor_aplicado DECIMAL(15, 2) NOT NULL,
            rentabilidade DECIMAL(8, 4),
            data_aplicacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cursor.close()
    conn.commit()


def _ensure_usuario_tipo_column(conn) -> None:
    cursor = conn.cursor()
    if not _table_exists(cursor, "usuarios"):
        cursor.close()
        return
    if not _column_exists(cursor, "usuarios", "tipo_usuario"):
        cursor.execute(
            "ALTER TABLE usuarios "
            "ADD COLUMN tipo_usuario VARCHAR(20) NOT NULL DEFAULT 'client'"
        )
        conn.commit()
    cursor.close()


def _normalize_usuario_tipo_values(conn) -> None:
    cursor = conn.cursor()
    if not _table_exists(cursor, "usuarios"):
        cursor.close()
        return
    cursor.execute(
        "UPDATE usuarios SET tipo_usuario = 'manager' "
        "WHERE UPPER(tipo_usuario) = 'MANAGER'"
    )
    cursor.execute(
        "UPDATE usuarios SET tipo_usuario = 'client' "
        "WHERE tipo_usuario IS NULL OR UPPER(tipo_usuario) = 'CLIENT'"
    )
    cursor.execute(
        "UPDATE usuarios SET tipo_usuario = 'client' "
        "WHERE LOWER(tipo_usuario) NOT IN ('client', 'manager')"
    )
    conn.commit()
    cursor.close()


def _ensure_audit_columns(conn) -> None:
    cursor = conn.cursor()
    target_tables = ["usuarios", "contas", "transacoes", "investimentos"]
    for table_name in sorted(target_tables):
        if not _table_exists(cursor, table_name):
            continue
        if not _column_exists(cursor, table_name, "created_at"):
            cursor.execute(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )
        if not _column_exists(cursor, table_name, "updated_at"):
            cursor.execute(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN updated_at DATETIME NOT NULL "
                "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            )
    conn.commit()
    cursor.close()


def _drop_gastos_table_if_exists(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS gastos")
    conn.commit()
    cursor.close()


def _ensure_conta_schema_and_data(conn) -> None:
    cursor = conn.cursor()
    if not _table_exists(cursor, "contas"):
        cursor.close()
        return
    cursor.execute(
        "UPDATE contas SET tipo_conta = 'checking' "
        "WHERE tipo_conta IS NULL OR LOWER(tipo_conta) IN ('corrente', 'checkings')"
    )
    cursor.execute(
        "UPDATE contas SET tipo_conta = 'savings' "
        "WHERE LOWER(tipo_conta) IN ('poupanca')"
    )
    cursor.execute(
        "UPDATE contas SET tipo_conta = 'checking' "
        "WHERE LOWER(tipo_conta) NOT IN ('checking', 'savings')"
    )
    cursor.execute(
        "UPDATE contas SET numero_conta = LPAD(CAST(id AS CHAR), 10, '0') "
        "WHERE numero_conta IS NULL OR numero_conta = '' OR numero_conta REGEXP '[^0-9]'"
    )
    cursor.execute(
        "UPDATE contas SET numero_conta = LPAD(numero_conta, 10, '0') "
        "WHERE numero_conta REGEXP '^[0-9]+$' AND CHAR_LENGTH(numero_conta) < 10"
    )
    cursor.execute(
        "UPDATE contas SET agencia = '0001' "
        "WHERE agencia IS NULL OR agencia = '' OR agencia REGEXP '[^0-9]' "
        "OR CHAR_LENGTH(agencia) <> 4"
    )
    cursor.execute(
        "ALTER TABLE contas MODIFY COLUMN numero_conta VARCHAR(10) NOT NULL"
    )
    cursor.execute(
        "ALTER TABLE contas MODIFY COLUMN agencia VARCHAR(4) NOT NULL DEFAULT '0001'"
    )
    cursor.execute(
        "ALTER TABLE contas MODIFY COLUMN tipo_conta "
        "ENUM('checking', 'savings') NOT NULL DEFAULT 'checking'"
    )
    conn.commit()
    cursor.close()


def _seed_default_users_if_empty(conn) -> None:
    from server.repositories.usuario_repository import UsuarioRepository

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    UsuarioRepository.create(
        conn,
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
        conn,
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
    conn.commit()


def init_db() -> None:
    conn = _get_pool().get_connection()
    try:
        _create_tables(conn)
        _ensure_usuario_tipo_column(conn)
        _normalize_usuario_tipo_values(conn)
        _ensure_audit_columns(conn)
        _ensure_conta_schema_and_data(conn)
        _drop_gastos_table_if_exists(conn)
        _seed_default_users_if_empty(conn)
    finally:
        conn.close()
