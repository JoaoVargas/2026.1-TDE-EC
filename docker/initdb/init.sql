-- BetaBank Digital — initial schema
-- Executed automatically by MySQL on first container start (empty data volume).

CREATE TABLE IF NOT EXISTS usuarios (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  NOT NULL UNIQUE,
    senha         VARCHAR(255)  NOT NULL,
    data_nascimento DATE         NOT NULL,
    cpf           VARCHAR(14)   NOT NULL UNIQUE,
    cep           VARCHAR(9)    NOT NULL,
    logradouro    VARCHAR(200),
    numero        VARCHAR(10),
    bairro        VARCHAR(100),
    cidade        VARCHAR(100),
    estado        VARCHAR(2),
    tipo_usuario  VARCHAR(20)   NOT NULL DEFAULT 'client',
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contas (
    id            INT               AUTO_INCREMENT PRIMARY KEY,
    usuario_id    INT               NOT NULL,
    numero_conta  VARCHAR(10)       NOT NULL UNIQUE,
    agencia       VARCHAR(4)        NOT NULL DEFAULT '0001',
    saldo         DECIMAL(15, 2)    NOT NULL DEFAULT 0.00,
    tipo_conta    ENUM('checking', 'savings') NOT NULL DEFAULT 'checking',
    created_at    DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS transacoes (
    id              INT             AUTO_INCREMENT PRIMARY KEY,
    conta_id        INT             NOT NULL,
    tipo_transacao  VARCHAR(30)     NOT NULL,
    descricao       VARCHAR(255),
    valor           DECIMAL(15, 2)  NOT NULL,
    data_transacao  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (conta_id) REFERENCES contas(id)
);

CREATE TABLE IF NOT EXISTS investimentos (
    id                  INT             AUTO_INCREMENT PRIMARY KEY,
    usuario_id          INT             NOT NULL,
    tipo_investimento   VARCHAR(50)     NOT NULL,
    nome_ativo          VARCHAR(100)    NOT NULL,
    valor_aplicado      DECIMAL(15, 2)  NOT NULL,
    rentabilidade       DECIMAL(8, 4),
    data_aplicacao      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
