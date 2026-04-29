from datetime import date

import mysql.connector

from server.core.security import hash_password
from server.db.connection import _get_pool
from server.models.user import UserType


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
        (table_name,),
    )
    return cursor.fetchone()[0] > 0


def _create_tables(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            id           INT           AUTO_INCREMENT PRIMARY KEY,
            cep          VARCHAR(8)    NOT NULL,
            street       VARCHAR(200)  NOT NULL,
            state        VARCHAR(2)    NOT NULL,
            city         VARCHAR(100)  NOT NULL,
            neighborhood VARCHAR(100)  NOT NULL,
            number       VARCHAR(10)   NOT NULL,
            created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INT           AUTO_INCREMENT PRIMARY KEY,
            cpf          VARCHAR(11)   NOT NULL UNIQUE,
            type         ENUM('client', 'manager') NOT NULL DEFAULT 'client',
            name         VARCHAR(100)  NOT NULL,
            email        VARCHAR(150)  NOT NULL UNIQUE,
            password     VARCHAR(255)  NOT NULL,
            birthday     DATE          NOT NULL,
            address_id   INT           NOT NULL,
            created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (address_id) REFERENCES addresses(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id             INT               AUTO_INCREMENT PRIMARY KEY,
            user_id        INT               NOT NULL,
            type           ENUM('checking', 'savings') NOT NULL DEFAULT 'checking',
            account_number VARCHAR(10)       NOT NULL UNIQUE,
            agency         VARCHAR(4)        NOT NULL DEFAULT '0001',
            balance        DECIMAL(15, 2)    NOT NULL DEFAULT 0.00,
            created_at     DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at     DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INT             AUTO_INCREMENT PRIMARY KEY,
            type            ENUM('internal', 'transaction', 'expense', 'other') NOT NULL,
            from_account_id INT,
            to_account_id   INT,
            amount          DECIMAL(15, 2)  NOT NULL,
            description     VARCHAR(255),
            created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (from_account_id) REFERENCES accounts(id),
            FOREIGN KEY (to_account_id) REFERENCES accounts(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id          INT             AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100)    NOT NULL,
            stock_code  VARCHAR(20)     NOT NULL,
            stock_name  VARCHAR(100)    NOT NULL,
            stock_price DECIMAL(15, 2)  NOT NULL,
            created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manager_portfolios (
            id           INT      AUTO_INCREMENT PRIMARY KEY,
            portfolio_id INT      NOT NULL,
            manager_id   INT      NOT NULL,
            created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (manager_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_portfolios (
            id           INT             AUTO_INCREMENT PRIMARY KEY,
            portfolio_id INT             NOT NULL,
            user_id      INT             NOT NULL,
            stock_amount DECIMAL(15, 4)  NOT NULL DEFAULT 0.0000,
            created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.close()
    conn.commit()


def _seed_default_users_if_empty(conn) -> None:
    from server.repositories.address_repository import AddressRepository
    from server.repositories.user_repository import UserRepository

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    manager_address = AddressRepository.create(
        conn,
        cep="80000000",
        street="Rua Gerente",
        state="PR",
        city="Curitiba",
        neighborhood="Centro",
        number="100",
    )
    UserRepository.create(
        conn,
        cpf="39053344705",
        type=UserType.MANAGER,
        name="Gerente Padrao",
        email="gerente@gerente.com",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1988, 1, 10),
        address_id=manager_address.id,
    )

    client_address = AddressRepository.create(
        conn,
        cep="80010000",
        street="Rua Cliente",
        state="PR",
        city="Curitiba",
        neighborhood="Batel",
        number="200",
    )
    UserRepository.create(
        conn,
        cpf="11144477735",
        type=UserType.CLIENT,
        name="Usuario Padrao",
        email="usuario@usuario.com",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1995, 5, 20),
        address_id=client_address.id,
    )
    conn.commit()


def init_db() -> None:
    conn = _get_pool().get_connection()
    try:
        _create_tables(conn)
        _seed_default_users_if_empty(conn)
    finally:
        conn.close()
