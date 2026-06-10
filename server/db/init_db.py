from datetime import date
from decimal import Decimal

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
        cep="80420090",
        street="Av. Batel",
        state="PR",
        city="Curitiba",
        neighborhood="Batel",
        number="1320",
    )
    UserRepository.create(
        conn,
        cpf="39053344705",
        type=UserType.MANAGER,
        name="Ricardo Alves Ferreira",
        email="gerente@gerente.com",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1982, 3, 15),
        address_id=manager_address.id,
    )

    mariana_address = AddressRepository.create(
        conn,
        cep="80020310",
        street="Rua XV de Novembro",
        state="PR",
        city="Curitiba",
        neighborhood="Centro",
        number="458",
    )
    UserRepository.create(
        conn,
        cpf="11144477735",
        type=UserType.CLIENT,
        name="Mariana Costa Oliveira",
        email="usuario@usuario.com",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1993, 7, 22),
        address_id=mariana_address.id,
    )

    pedro_address = AddressRepository.create(
        conn,
        cep="80060240",
        street="Rua Padre Camargo",
        state="PR",
        city="Curitiba",
        neighborhood="Alto da Glória",
        number="280",
    )
    UserRepository.create(
        conn,
        cpf="98765432100",
        type=UserType.CLIENT,
        name="Pedro Henrique Santos",
        email="pedro.h.santos@betabank.com.br",
        password_hash=hash_password("ASDasd123"),
        birthday=date(1989, 11, 5),
        address_id=pedro_address.id,
    )

    conn.commit()


def _insert_tx(cursor, *, type, from_id, to_id, amount, description, days_ago=0):
    if days_ago == 0:
        cursor.execute(
            "INSERT INTO transactions (type, from_account_id, to_account_id, amount, description) "
            "VALUES (%s, %s, %s, %s, %s)",
            (type, from_id, to_id, str(amount), description),
        )
    else:
        cursor.execute(
            "INSERT INTO transactions "
            "(type, from_account_id, to_account_id, amount, description, created_at) "
            "VALUES (%s, %s, %s, %s, %s, DATE_SUB(NOW(), INTERVAL %s DAY))",
            (type, from_id, to_id, str(amount), description, days_ago),
        )


def _seed_transactions_if_empty(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT a.id AS account_id FROM users u "
        "JOIN accounts a ON a.user_id = u.id AND a.type = 'checking' "
        "WHERE u.email = 'usuario@usuario.com'"
    )
    mariana_row = cursor.fetchone()
    cursor.execute(
        "SELECT a.id AS account_id FROM users u "
        "JOIN accounts a ON a.user_id = u.id AND a.type = 'checking' "
        "WHERE u.email = 'pedro.h.santos@betabank.com.br'"
    )
    pedro_row = cursor.fetchone()
    cursor.close()

    if not mariana_row or not pedro_row:
        return

    m = mariana_row["account_id"]
    p = pedro_row["account_id"]

    cursor = conn.cursor()

    # --- Mariana ---
    # May salary deposit
    _insert_tx(cursor, type="deposit", from_id=None, to_id=m, amount=Decimal("8500.00"),
               description="Salário - maio/2026", days_ago=42)
    # Rent May
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("1200.00"),
               description="Aluguel - maio/2026", days_ago=41)
    # Electricity via PIX
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("187.50"),
               description="PIX - Copel energia elétrica", days_ago=38)
    # PIX transfer to Pedro
    _insert_tx(cursor, type="transaction", from_id=m, to_id=p, amount=Decimal("300.00"),
               description="PIX - Pedro Henrique Santos", days_ago=35)
    # ATM cash withdrawal
    _insert_tx(cursor, type="withdrawal", from_id=m, to_id=None, amount=Decimal("400.00"),
               description="Saque - Caixa Eletrônico Banco24h", days_ago=30)
    # Streaming subscriptions
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("89.90"),
               description="Netflix e Spotify - assinaturas mensais", days_ago=28)
    # June salary deposit
    _insert_tx(cursor, type="deposit", from_id=None, to_id=m, amount=Decimal("8500.00"),
               description="Salário - junho/2026", days_ago=12)
    # Rent June
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("1200.00"),
               description="Aluguel - junho/2026", days_ago=11)
    # Internet via PIX
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("99.90"),
               description="PIX - Vivo internet fibra", days_ago=8)
    # Investment application (ITUB4 40 shares × R$34.70 + SELIC29 70 units × R$13.24 = R$2,314.80)
    _insert_tx(cursor, type="other", from_id=m, to_id=None, amount=Decimal("2314.80"),
               description="Aplicação em investimentos - ITUB4 e SELIC29", days_ago=7)
    # PIX transfer to Pedro
    _insert_tx(cursor, type="transaction", from_id=m, to_id=p, amount=Decimal("150.00"),
               description="PIX - Pedro Henrique Santos", days_ago=5)
    # Grocery
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("347.60"),
               description="Supermercado Condor - compras da semana", days_ago=3)
    # Credit card payment
    _insert_tx(cursor, type="expense", from_id=m, to_id=None, amount=Decimal("500.00"),
               description="Pagamento fatura cartão de crédito", days_ago=2)

    # --- Pedro ---
    # May salary deposit
    _insert_tx(cursor, type="deposit", from_id=None, to_id=p, amount=Decimal("5000.00"),
               description="Salário - maio/2026", days_ago=42)
    # Rent May
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("800.00"),
               description="Aluguel - maio/2026", days_ago=41)
    # Grocery May (PIX from Mariana at days_ago=35 already covers the credit entry)
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("256.30"),
               description="Supermercado Walmart - compras", days_ago=30)
    # Gas bill via PIX
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("185.00"),
               description="PIX - Comgás conta gás", days_ago=25)
    # Water bill via PIX
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("73.20"),
               description="PIX - Sanepar água e esgoto", days_ago=20)
    # June salary deposit
    _insert_tx(cursor, type="deposit", from_id=None, to_id=p, amount=Decimal("5000.00"),
               description="Salário - junho/2026", days_ago=12)
    # Rent June
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("800.00"),
               description="Aluguel - junho/2026", days_ago=11)
    # Investment application (PETR4 40 × R$36.85 + BTC 0.003 × R$325,000 = R$2,449.00)
    _insert_tx(cursor, type="other", from_id=p, to_id=None, amount=Decimal("2449.00"),
               description="Aplicação em investimentos - PETR4 e BTC", days_ago=10)
    # Grocery June
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("195.80"),
               description="Supermercado Condor - compras da semana", days_ago=3)
    # Pharmacy
    _insert_tx(cursor, type="expense", from_id=p, to_id=None, amount=Decimal("87.40"),
               description="Farmácia Nissei - medicamentos", days_ago=1)

    cursor.close()

    # Final balances derived from the transactions above:
    # Mariana: +8500 -1200 -187.50 -300 -400 -89.90 +8500 -1200 -99.90 -2314.80 -150 -347.60 -500 = R$10,210.30
    # Pedro:   +5000 -800 +300 -256.30 -185 -73.20 +5000 -800 -2449 +150 -195.80 -87.40 = R$5,603.30
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s", (Decimal("10210.30"), m))
    cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s", (Decimal("5603.30"), p))
    cursor.close()
    conn.commit()


def _seed_credit_cards_if_empty(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM credit_cards")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    from server.repositories.credit_card_repository import CreditCardRepository

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = 'usuario@usuario.com'")
    mariana_row = cursor.fetchone()
    cursor.close()

    if not mariana_row:
        return

    card = CreditCardRepository.create(
        conn,
        user_id=mariana_row["id"],
        card_name="MARIANA C OLIVEIRA",
        limit_amount=Decimal("8000.00"),
        due_day=15,
    )

    # Purchases with backdated timestamps
    purchases = [
        (Decimal("299.90"), "Amazon - acessórios notebook", 25),
        (Decimal("89.00"),  "Uber Eats - restaurante japonês", 20),
        (Decimal("450.00"), "Renner - roupas e calçados", 15),
        (Decimal("120.50"), "iFood - jantar delivery", 8),
        (Decimal("67.80"),  "Posto Ipiranga - combustível", 6),
    ]

    cursor = conn.cursor()
    for amount, desc, days_ago in purchases:
        cursor.execute(
            "INSERT INTO credit_card_transactions "
            "(credit_card_id, type, amount, description, created_at) "
            "VALUES (%s, 'purchase', %s, %s, DATE_SUB(NOW(), INTERVAL %s DAY))",
            (card.id, str(amount), desc, days_ago),
        )
        CreditCardRepository.apply_purchase(conn, card_id=card.id, amount=amount)

    # Partial payment
    payment = Decimal("500.00")
    cursor.execute(
        "INSERT INTO credit_card_transactions "
        "(credit_card_id, type, amount, description, created_at) "
        "VALUES (%s, 'payment', %s, 'Pagamento fatura', DATE_SUB(NOW(), INTERVAL 2 DAY))",
        (card.id, str(payment)),
    )
    CreditCardRepository.apply_payment(conn, card_id=card.id, amount=payment)

    cursor.close()
    conn.commit()


def _seed_investments_if_empty(conn) -> None:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_portfolios")
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return

    from server.repositories.portfolio_repository import PortfolioRepository
    from server.repositories.user_portfolio_repository import UserPortfolioRepository

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = 'usuario@usuario.com'")
    mariana_row = cursor.fetchone()
    cursor.execute("SELECT id FROM users WHERE email = 'pedro.h.santos@betabank.com.br'")
    pedro_row = cursor.fetchone()
    cursor.close()

    if not mariana_row or not pedro_row:
        return

    portfolios = {p.stock_code: p for p in PortfolioRepository.list_all(conn)}

    # Mariana: ITUB4 40 shares (40 × R$34.70 = R$1,388) + SELIC29 70 units (70 × R$13.24 = R$926.80)
    if "ITUB4" in portfolios:
        UserPortfolioRepository.create(
            conn,
            portfolio_id=portfolios["ITUB4"].id,
            user_id=mariana_row["id"],
            stock_amount=Decimal("40.0000"),
        )
    if "SELIC29" in portfolios:
        UserPortfolioRepository.create(
            conn,
            portfolio_id=portfolios["SELIC29"].id,
            user_id=mariana_row["id"],
            stock_amount=Decimal("70.0000"),
        )

    # Pedro: PETR4 40 shares (40 × R$36.85 = R$1,474) + BTC 0.003 (0.003 × R$325,000 = R$975)
    if "PETR4" in portfolios:
        UserPortfolioRepository.create(
            conn,
            portfolio_id=portfolios["PETR4"].id,
            user_id=pedro_row["id"],
            stock_amount=Decimal("40.0000"),
        )
    if "BTC" in portfolios:
        UserPortfolioRepository.create(
            conn,
            portfolio_id=portfolios["BTC"].id,
            user_id=pedro_row["id"],
            stock_amount=Decimal("0.0030"),
        )

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
        _seed_transactions_if_empty(conn)
        _seed_credit_cards_if_empty(conn)
        _seed_investments_if_empty(conn)
    finally:
        conn.close()
