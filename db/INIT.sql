-- =============================================
-- Script SQL - Sistema Bancário Digital
-- Projeto Acadêmico - Python + Flask + MySQL
-- =============================================

CREATE DATABASE IF NOT EXISTS bancodigital
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE bancodigital;

-- =============================================
-- Tabela: usuarios
-- =============================================
CREATE TABLE IF NOT EXISTS usuarios (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome             VARCHAR(100)   NOT NULL,
    email            VARCHAR(150)   NOT NULL UNIQUE,
    -- ATENÇÃO: Em produção real, NUNCA armazene senha em texto puro.
    -- Use hashing com bcrypt ou argon2. Aqui é texto puro só para fins acadêmicos.
    senha            VARCHAR(255)   NOT NULL,
    data_nascimento  DATE           NOT NULL,
    cpf              VARCHAR(14)    NOT NULL UNIQUE,
    cep              VARCHAR(9)     NOT NULL,
    logradouro       VARCHAR(200),
    numero           VARCHAR(10),
    bairro           VARCHAR(100),
    cidade           VARCHAR(100),
    estado           VARCHAR(2),
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Tabela: contas
-- =============================================
CREATE TABLE IF NOT EXISTS contas (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id   BIGINT          NOT NULL,
    numero_conta VARCHAR(20)     NOT NULL UNIQUE,
    agencia      VARCHAR(10)     NOT NULL DEFAULT '0001',
    saldo        DECIMAL(15,2)   NOT NULL DEFAULT 0.00,
    tipo_conta   VARCHAR(30)     NOT NULL DEFAULT 'CORRENTE',
    CONSTRAINT fk_conta_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Tabela: transacoes
-- =============================================
CREATE TABLE IF NOT EXISTS transacoes (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    conta_id        BIGINT          NOT NULL,
    tipo_transacao  VARCHAR(30)     NOT NULL,   -- ENTRADA ou SAIDA
    descricao       VARCHAR(255),
    valor           DECIMAL(15,2)   NOT NULL,
    data_transacao  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transacao_conta FOREIGN KEY (conta_id) REFERENCES contas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Tabela: gastos
-- =============================================
CREATE TABLE IF NOT EXISTS gastos (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  BIGINT          NOT NULL,
    categoria   VARCHAR(50)     NOT NULL,
    descricao   VARCHAR(255),
    valor       DECIMAL(15,2)   NOT NULL,
    data_gasto  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_gasto_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Tabela: investimentos
-- =============================================
CREATE TABLE IF NOT EXISTS investimentos (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id        BIGINT          NOT NULL,
    tipo_investimento VARCHAR(50)     NOT NULL,
    nome_ativo        VARCHAR(100)    NOT NULL,
    valor_aplicado    DECIMAL(15,2)   NOT NULL,
    rentabilidade     DECIMAL(8,4),
    data_aplicacao    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_investimento_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;