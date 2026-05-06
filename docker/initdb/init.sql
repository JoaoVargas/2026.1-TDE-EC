-- BetaBank Digital — initial schema
-- Executed automatically by MySQL on first container start (empty data volume).

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
);

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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS portfolios (
    id          INT             AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    stock_code  VARCHAR(20)     NOT NULL,
    stock_name  VARCHAR(100)    NOT NULL,
    stock_price DECIMAL(15, 2)  NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manager_portfolios (
    id           INT      AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT      NOT NULL,
    manager_id   INT      NOT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_portfolios (
    id           INT             AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT             NOT NULL,
    user_id      INT             NOT NULL,
    stock_amount DECIMAL(15, 4)  NOT NULL DEFAULT 0.0000,
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

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
);
