from datetime import date
from decimal import Decimal

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
            type            ENUM('internal', 'transaction', 'expense', 'other', 'deposit', 'withdrawal') NOT NULL,
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_price_history (
            id           INT             AUTO_INCREMENT PRIMARY KEY,
            portfolio_id INT             NOT NULL,
            price        DECIMAL(15, 4)  NOT NULL,
            recorded_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
            INDEX idx_pph_portfolio_time (portfolio_id, recorded_at)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          CHAR(64)     NOT NULL PRIMARY KEY,
            user_id     INT          NOT NULL,
            expires_at  DATETIME     NOT NULL,
            ip_address  VARCHAR(45)  NULL,
            user_agent  VARCHAR(512) NULL,
            created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sessions_user_id (user_id),
            INDEX idx_sessions_expires_at (expires_at),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_avatars (
            id          INT          AUTO_INCREMENT PRIMARY KEY,
            user_id     INT          NOT NULL UNIQUE,
            image_data  MEDIUMBLOB   NOT NULL,
            mime_type   VARCHAR(50)  NOT NULL,
            created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id            INT             AUTO_INCREMENT PRIMARY KEY,
            user_id       INT             NOT NULL UNIQUE,
            card_number   VARCHAR(16)     NOT NULL UNIQUE,
            card_name     VARCHAR(100)    NOT NULL,
            limit_amount  DECIMAL(15, 2)  NOT NULL DEFAULT 5000.00,
            used_amount   DECIMAL(15, 2)  NOT NULL DEFAULT 0.00,
            due_day       INT             NOT NULL DEFAULT 10,
            status        ENUM('active', 'blocked') NOT NULL DEFAULT 'active',
            created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_card_transactions (
            id              INT             AUTO_INCREMENT PRIMARY KEY,
            credit_card_id  INT             NOT NULL,
            type            ENUM('purchase', 'payment') NOT NULL DEFAULT 'purchase',
            amount          DECIMAL(15, 2)  NOT NULL,
            description     VARCHAR(255),
            created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (credit_card_id) REFERENCES credit_cards(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pix_keys (
            id          INT          AUTO_INCREMENT PRIMARY KEY,
            user_id     INT          NOT NULL,
            account_id  INT          NOT NULL,
            key_type    ENUM('cpf', 'email', 'phone', 'random') NOT NULL,
            key_value   VARCHAR(150) NOT NULL UNIQUE,
            created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
            INDEX idx_pix_user (user_id)
        )
    """)
    cursor.close()
    conn.commit()


def _seed_default_users_if_empty(conn) -> None:
    from server.models.account import AccountType
    from server.repositories.account_repository import AccountRepository
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
    client = UserRepository.create(
        conn,
        cpf="11144477735",
        type=UserType.CLIENT,
        name="Usuario Padrao",
        email="usuario@usuario.com",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1995, 5, 20),
        address_id=client_address.id,
    )

    checking = AccountRepository.get_by_user_and_type(conn, client.id, AccountType.CHECKING)
    if checking:
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s", (Decimal("1000.00"), checking.id))
        cursor.close()

    conn.commit()


def _seed_portfolios_if_empty(conn) -> None:
    from server.repositories.manager_portfolio_repository import ManagerPortfolioRepository
    from server.repositories.portfolio_repository import PortfolioRepository

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM portfolios")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE type = 'manager' LIMIT 1")
    manager = cursor.fetchone()
    cursor.close()

    # (class, stock_code, stock_name, current_price, [(days_ago, price), ...])
    _portfolios = [
        (
            "Renda fixa", "CDBBB", "CDB BetaBank", Decimal("10.52"),
            [(90,"10.00"),(78,"10.04"),(66,"10.09"),(54,"10.14"),(42,"10.19"),
             (30,"10.24"),(20,"10.31"),(12,"10.37"),(6,"10.43"),(2,"10.49"),(0,"10.52")],
        ),
        (
            "Renda fixa", "SELIC29", "Tesouro SELIC 2029", Decimal("13.24"),
            [(90,"12.50"),(78,"12.60"),(66,"12.71"),(54,"12.82"),(42,"12.93"),
             (30,"13.04"),(20,"13.10"),(12,"13.16"),(6,"13.20"),(2,"13.22"),(0,"13.24")],
        ),
        (
            "Renda variavel", "PETR4", "Petrobras PN", Decimal("36.85"),
            [(90,"40.10"),(78,"38.50"),(66,"41.20"),(54,"39.80"),(42,"43.50"),
             (30,"37.90"),(20,"35.40"),(12,"33.20"),(6,"34.60"),(2,"35.90"),(0,"36.85")],
        ),
        (
            "Renda variavel", "VALE3", "Vale ON", Decimal("65.50"),
            [(90,"58.30"),(78,"61.40"),(66,"59.80"),(54,"62.70"),(42,"60.10"),
             (30,"63.50"),(20,"62.90"),(12,"64.20"),(6,"65.80"),(2,"65.20"),(0,"65.50")],
        ),
        (
            "Renda variavel", "ITUB4", "Itaú Unibanco PN", Decimal("34.70"),
            [(90,"30.50"),(78,"31.20"),(66,"29.80"),(54,"32.10"),(42,"31.70"),
             (30,"33.20"),(20,"32.90"),(12,"33.80"),(6,"34.10"),(2,"34.50"),(0,"34.70")],
        ),
        (
            "Criptomoedas", "BTC", "Bitcoin", Decimal("325000.00"),
            [(90,"285000.00"),(78,"305000.00"),(66,"278000.00"),(54,"315000.00"),(42,"292000.00"),
             (30,"308000.00"),(20,"318000.00"),(12,"298000.00"),(6,"312000.00"),(2,"320000.00"),(0,"325000.00")],
        ),
        (
            "Criptomoedas", "ETH", "Ethereum", Decimal("18500.00"),
            [(90,"14800.00"),(78,"16200.00"),(66,"15100.00"),(54,"17500.00"),(42,"16800.00"),
             (30,"18200.00"),(20,"17600.00"),(12,"18900.00"),(6,"18200.00"),(2,"18600.00"),(0,"18500.00")],
        ),
    ]

    for cls, stock_code, stock_name, current_price, history in _portfolios:
        portfolio = PortfolioRepository.create(
            conn,
            name=cls,
            stock_code=stock_code,
            stock_name=stock_name,
            stock_price=current_price,
        )

        if manager:
            ManagerPortfolioRepository.create(conn, portfolio_id=portfolio.id, manager_id=manager["id"])

        cursor = conn.cursor()
        for days_ago, price in history:
            if days_ago == 0:
                cursor.execute(
                    "INSERT INTO portfolio_price_history (portfolio_id, price) VALUES (%s, %s)",
                    (portfolio.id, price),
                )
            else:
                cursor.execute(
                    "INSERT INTO portfolio_price_history (portfolio_id, price, recorded_at) "
                    "VALUES (%s, %s, DATE_SUB(NOW(), INTERVAL %s DAY))",
                    (portfolio.id, price, days_ago),
                )
        cursor.close()

    conn.commit()


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, column),
    )
    return cursor.fetchone()[0] > 0


def _enum_has_value(cursor, table: str, column: str, value: str) -> bool:
    cursor.execute(
        "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, column),
    )
    row = cursor.fetchone()
    return row is not None and value in row[0]


def _apply_migrations(conn) -> None:
    cursor = conn.cursor()

    if not _enum_has_value(cursor, "transactions", "type", "deposit"):
        cursor.execute(
            "ALTER TABLE transactions MODIFY COLUMN type "
            "ENUM('internal','transaction','expense','other','deposit','withdrawal') NOT NULL"
        )
        conn.commit()

    cursor.execute(
        "INSERT INTO portfolio_price_history (portfolio_id, price, recorded_at) "
        "SELECT id, stock_price, created_at FROM portfolios "
        "WHERE id NOT IN (SELECT DISTINCT portfolio_id FROM portfolio_price_history)"
    )
    conn.commit()

    if _table_exists(cursor, "pix_keys"):
        cursor.execute(
            "SELECT u.id, u.cpf, u.email FROM users u "
            "WHERE u.type = 'client' AND u.id NOT IN (SELECT DISTINCT user_id FROM pix_keys)"
        )
        users_without_pix = cursor.fetchall()
        for user_id, cpf, email in users_without_pix:
            cursor.execute(
                "SELECT id FROM accounts WHERE user_id = %s AND type = 'checking' LIMIT 1",
                (user_id,),
            )
            acc_row = cursor.fetchone()
            if not acc_row:
                continue
            account_id = acc_row[0]
            for key_type, key_value in [("cpf", cpf), ("email", email.lower())]:
                cursor.execute("SELECT COUNT(*) FROM pix_keys WHERE key_value = %s", (key_value,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO pix_keys (user_id, account_id, key_type, key_value) VALUES (%s, %s, %s, %s)",
                        (user_id, account_id, key_type, key_value),
                    )
        if users_without_pix:
            conn.commit()

    cursor.close()


def init_db() -> None:
    conn = _get_pool().get_connection()
    try:
        _create_tables(conn)
        _seed_default_users_if_empty(conn)
        _apply_migrations(conn)
        _seed_portfolios_if_empty(conn)
    finally:
        conn.close()
