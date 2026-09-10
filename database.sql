-- Active: 1768952423418@@127.0.0.1@5432@zelus


-- ==============================================================================
-- 1. CRIAÇÃO DOS TIPOS ENUM (Domínios restritos)
-- ==============================================================================

CREATE TYPE perfil_usuario AS ENUM ('Morador', 'Sindico', 'Administrador');
CREATE TYPE status_chamado AS ENUM ('Aberto', 'Em Andamento', 'Resolvido', 'Cancelado');
CREATE TYPE status_aprovacao AS ENUM ('Pendente', 'Aprovado', 'Rejeitado');

-- ==============================================================================
-- 2. CRIAÇÃO DAS TABELAS
-- ==============================================================================

-- Tabela de Usuários (Moradores, Síndicos e Administradores)
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil perfil_usuario NOT NULL,
    senha_provisoria BOOLEAN DEFAULT FALSE,
    token_validacao VARCHAR(255),
    excluido_logicamente BOOLEAN DEFAULT FALSE
);

-- Tabela de Condomínios
CREATE TABLE condominio (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco TEXT NOT NULL,
    id_sindico INT UNIQUE NOT NULL, -- Relacionamento 1:1 com o Síndico
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_condominio_sindico FOREIGN KEY (id_sindico) REFERENCES usuario(id)
);

-- Tabela de Unidades (Apartamentos/Blocos)
CREATE TABLE unidade (
    id SERIAL PRIMARY KEY,
    id_condominio INT NOT NULL,
    bloco VARCHAR(50),
    apartamento VARCHAR(50) NOT NULL,
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_unidade_condominio FOREIGN KEY (id_condominio) REFERENCES condominio(id)
);

-- Tabela de Vínculo entre Morador e Unidade (N:N com status de aprovação)
CREATE TABLE vinculo_morador_unidade (
    id SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_unidade INT NOT NULL,
    status_aprovacao status_aprovacao DEFAULT 'Pendente',
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_vinculo_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id),
    CONSTRAINT fk_vinculo_unidade FOREIGN KEY (id_unidade) REFERENCES unidade(id),
    CONSTRAINT uk_usuario_unidade UNIQUE (id_usuario, id_unidade) -- Evita duplicidade de solicitação
);

-- Tabela de Categorias de Chamados (Personalizada por condomínio)
CREATE TABLE categoria_chamado (
    id SERIAL PRIMARY KEY,
    id_condominio INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    prazo_sla INTERVAL NOT NULL, -- Usando INTERVAL para representar dias/horas (ex: '24 hours', '3 days')
    ativo BOOLEAN DEFAULT TRUE,
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_categoria_condominio FOREIGN KEY (id_condominio) REFERENCES condominio(id)

);

-- Tabela de Chamados
CREATE TABLE chamado (
    id SERIAL PRIMARY KEY, -- Funciona também como o número do ticket
    id_usuario_autor INT NOT NULL,
    id_unidade_destino INT NOT NULL,
    id_categoria INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    foto_url VARCHAR(255),
    video_url VARCHAR(255),
    prazo_sla_vigente INTERVAL NOT NULL,
    status status_chamado DEFAULT 'Aberto',
    data_visto TIMESTAMP,
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_chamado_usuario FOREIGN KEY (id_usuario_autor) REFERENCES usuario(id),
    CONSTRAINT fk_chamado_unidade FOREIGN KEY (id_unidade_destino) REFERENCES unidade(id),
    CONSTRAINT fk_chamado_categoria FOREIGN KEY (id_categoria) REFERENCES categoria_chamado(id)
);

-- Tabela de Histórico do Chamado (Log de alterações de status)
CREATE TABLE historico_chamado (
    id SERIAL PRIMARY KEY,
    id_chamado INT NOT NULL,
    data_alteracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_anterior status_chamado NOT NULL,
    novo_status status_chamado NOT NULL,
    observacao TEXT,
    excluido_logicamente BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_historico_chamado FOREIGN KEY (id_chamado) REFERENCES chamado(id)
);

ALTER TABLE categoria_chamado ADD COLUMN id_categoria INT;

DROP TABLE IF EXISTS usuario CASCADE;

select * from chamado;

DROP TABLE IF EXISTS vinculo_morador_unidade CASCADE;
