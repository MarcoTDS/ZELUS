-- =====================================================================
-- ZELUS - Script de criação do banco de dados (PostgreSQL)
-- Baseado no Dicionário de Dados (versão 3)
--
-- ATENÇÃO: este script RECRIA o schema do zero. Todas as tabelas e
-- tipos abaixo são removidos (DROP ... CASCADE) e os dados existentes
-- serão perdidos. Faça backup antes de executar em um banco com dados.
--
-- Execução:  psql -U <usuario> -d <banco> -f sql/zelus_schema.sql
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 0. Limpeza do modelo anterior
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS historico_chamado        CASCADE;
DROP TABLE IF EXISTS chamado                  CASCADE;
DROP TABLE IF EXISTS categoria_chamado        CASCADE;
DROP TABLE IF EXISTS usuario_unidade          CASCADE;
DROP TABLE IF EXISTS unidade                  CASCADE;
DROP TABLE IF EXISTS condominio               CASCADE;
DROP TABLE IF EXISTS usuario                  CASCADE;
-- Tabelas que existiam na modelagem antiga e saíram do dicionário
DROP TABLE IF EXISTS sindico_condominio       CASCADE;
DROP TABLE IF EXISTS vinculo_morador_unidade  CASCADE;

DROP TYPE IF EXISTS perfil_usuario    CASCADE;
DROP TYPE IF EXISTS tipo_condominio   CASCADE;
DROP TYPE IF EXISTS status_aprovacao  CASCADE;
DROP TYPE IF EXISTS status_chamado    CASCADE;
-- Tipos ENUM gerados automaticamente pelo SQLAlchemy na modelagem antiga
DROP TYPE IF EXISTS perfilusuarioenum CASCADE;
DROP TYPE IF EXISTS statusvinculoenum CASCADE;
DROP TYPE IF EXISTS status_anterior   CASCADE;
DROP TYPE IF EXISTS novo_status       CASCADE;

-- ---------------------------------------------------------------------
-- 1. Tipos ENUM
-- (valores iguais aos de models/enums.py e models/vinculo.py)
-- ---------------------------------------------------------------------
CREATE TYPE perfil_usuario   AS ENUM ('Morador', 'Sindico', 'Administrador');
CREATE TYPE tipo_condominio  AS ENUM ('Casa', 'Apartamento');
CREATE TYPE status_aprovacao AS ENUM ('Pendente', 'Aprovado', 'Rejeitado');
CREATE TYPE status_chamado   AS ENUM ('Aberto', 'Em Andamento', 'Resolvido', 'Cancelado');

-- ---------------------------------------------------------------------
-- 1.1 usuario
-- Armazena as credenciais e dados básicos de acesso de todos os atores.
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id             SERIAL                  PRIMARY KEY,
    nome           CHARACTER VARYING(150)  NOT NULL,
    email          CHARACTER VARYING(150)  NOT NULL UNIQUE,
    senha          CHARACTER VARYING(255)  NOT NULL,
    perfil         perfil_usuario          NOT NULL,
    ultimo_acesso  TIMESTAMP               DEFAULT NULL,
    ativo          BOOLEAN                 NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE  usuario               IS 'Credenciais e dados básicos de acesso de todos os atores.';
COMMENT ON COLUMN usuario.id            IS 'Identificador único do usuário.';
COMMENT ON COLUMN usuario.nome          IS 'Nome completo do usuário.';
COMMENT ON COLUMN usuario.email         IS 'E-mail para autenticação no sistema.';
COMMENT ON COLUMN usuario.senha         IS 'Senha criptografada do usuário.';
COMMENT ON COLUMN usuario.perfil        IS 'Define as permissões (Morador, Sindico, Administrador).';
COMMENT ON COLUMN usuario.ultimo_acesso IS 'Registro de data e hora do último login com sucesso.';
COMMENT ON COLUMN usuario.ativo         IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.2 condominio
-- ---------------------------------------------------------------------
CREATE TABLE condominio (
    id          SERIAL                  PRIMARY KEY,
    nome        CHARACTER VARYING(100)  NOT NULL,
    cep         CHARACTER VARYING(20)   NOT NULL,
    numero      CHARACTER VARYING(6)    NOT NULL,
    rua         CHARACTER VARYING(150)  NOT NULL,
    bairro      CHARACTER VARYING(100)  NOT NULL,
    cidade      CHARACTER VARYING(100)  NOT NULL,
    estado      CHARACTER(2)            NOT NULL,
    id_sindico  INT                     NOT NULL,
    ativo       BOOLEAN                 NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_condominio_sindico
        FOREIGN KEY (id_sindico) REFERENCES usuario (id)
);

COMMENT ON TABLE  condominio            IS 'Condomínios cadastrados no sistema.';
COMMENT ON COLUMN condominio.id         IS 'Identificador único do condomínio.';
COMMENT ON COLUMN condominio.nome       IS 'Nome do condomínio.';
COMMENT ON COLUMN condominio.cep        IS 'Código Postal do endereço.';
COMMENT ON COLUMN condominio.numero     IS 'Número do endereço do condomínio.';
COMMENT ON COLUMN condominio.rua        IS 'Logradouro do condomínio.';
COMMENT ON COLUMN condominio.bairro     IS 'Bairro de localização.';
COMMENT ON COLUMN condominio.cidade     IS 'Cidade de localização.';
COMMENT ON COLUMN condominio.estado     IS 'Sigla da Unidade Federativa (UF).';
COMMENT ON COLUMN condominio.id_sindico IS 'Chave estrangeira ligando ao responsável na tabela usuario.';
COMMENT ON COLUMN condominio.ativo      IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.3 unidade
-- Blocos/apartamentos ou ruas/casas vinculados ao condomínio.
-- ---------------------------------------------------------------------
CREATE TABLE unidade (
    id               SERIAL                  PRIMARY KEY,
    id_condominio    INT                     NOT NULL,
    tipo_condominio  tipo_condominio         NOT NULL,
    bloco            CHARACTER VARYING(50)   NULL,
    apartamento      CHARACTER VARYING(50)   NULL,
    rua              CHARACTER VARYING(150)  NULL,
    numero_casa      CHARACTER VARYING(50)   NULL,
    ativo            BOOLEAN                 NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_unidade_condominio
        FOREIGN KEY (id_condominio) REFERENCES condominio (id),

    -- Apartamento exige o número do apartamento; casa exige o número da casa
    CONSTRAINT ck_unidade_identificacao CHECK (
        (tipo_condominio = 'Apartamento' AND apartamento IS NOT NULL) OR
        (tipo_condominio = 'Casa'        AND numero_casa IS NOT NULL)
    )
);

COMMENT ON TABLE  unidade                 IS 'Blocos/apartamentos ou ruas/casas vinculados ao condomínio.';
COMMENT ON COLUMN unidade.id              IS 'Identificador único da unidade.';
COMMENT ON COLUMN unidade.id_condominio   IS 'Referência ao condomínio correspondente.';
COMMENT ON COLUMN unidade.tipo_condominio IS 'Define o tipo do condomínio, se é de casas ou apartamentos.';
COMMENT ON COLUMN unidade.bloco           IS 'Identificação de bloco/torre (uso comum em prédios).';
COMMENT ON COLUMN unidade.apartamento     IS 'Número do apartamento.';
COMMENT ON COLUMN unidade.rua             IS 'Nome da rua interna (uso comum em condomínios de casas).';
COMMENT ON COLUMN unidade.numero_casa     IS 'Número da residência (uso comum em condomínios de casas).';
COMMENT ON COLUMN unidade.ativo           IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.4 usuario_unidade
-- Tabela associativa que gerencia a aprovação e o vínculo de moradores.
-- ---------------------------------------------------------------------
CREATE TABLE usuario_unidade (
    id                SERIAL            PRIMARY KEY,
    id_usuario        INT               NOT NULL,
    id_unidade        INT               NOT NULL,
    status_aprovacao  status_aprovacao  NOT NULL DEFAULT 'Pendente',
    ativo             BOOLEAN           NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_usuario_unidade_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuario (id),
    CONSTRAINT fk_usuario_unidade_unidade
        FOREIGN KEY (id_unidade) REFERENCES unidade (id)
);

-- Impede dois vínculos ativos do mesmo morador com a mesma unidade
CREATE UNIQUE INDEX uq_usuario_unidade_ativo
    ON usuario_unidade (id_usuario, id_unidade)
    WHERE ativo = TRUE;

COMMENT ON TABLE  usuario_unidade                  IS 'Gerencia a aprovação e o vínculo de moradores às unidades.';
COMMENT ON COLUMN usuario_unidade.id               IS 'Identificador único do vínculo.';
COMMENT ON COLUMN usuario_unidade.id_usuario       IS 'Referência ao usuário (morador solicitante).';
COMMENT ON COLUMN usuario_unidade.id_unidade       IS 'Referência à unidade pretendida.';
COMMENT ON COLUMN usuario_unidade.status_aprovacao IS 'Fase do processo de autorização gerenciado pelo síndico.';
COMMENT ON COLUMN usuario_unidade.ativo            IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.5 categoria_chamado
-- Tipificações de problemas com prazos de atendimento (SLA).
-- ---------------------------------------------------------------------
CREATE TABLE categoria_chamado (
    id             SERIAL                  PRIMARY KEY,
    id_condominio  INT                     NOT NULL,
    nome           CHARACTER VARYING(100)  NOT NULL,
    prazo_sla      INTERVAL                NOT NULL,
    ativo          BOOLEAN                 NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_categoria_condominio
        FOREIGN KEY (id_condominio) REFERENCES condominio (id),
    CONSTRAINT ck_categoria_prazo_sla_positivo
        CHECK (prazo_sla > INTERVAL '0')
);

COMMENT ON TABLE  categoria_chamado               IS 'Tipificações de problemas com prazos de atendimento (SLA).';
COMMENT ON COLUMN categoria_chamado.id            IS 'Identificador único da categoria.';
COMMENT ON COLUMN categoria_chamado.id_condominio IS 'Referência ao condomínio que cadastrou a categoria.';
COMMENT ON COLUMN categoria_chamado.nome          IS 'Título da categoria (ex: Elétrica, Hidráulica).';
COMMENT ON COLUMN categoria_chamado.prazo_sla     IS 'Tempo máximo estipulado para a resolução.';
COMMENT ON COLUMN categoria_chamado.ativo         IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.6 chamado
-- Registros de atendimento (tickets) abertos pelos moradores.
-- ---------------------------------------------------------------------
CREATE TABLE chamado (
    id                  SERIAL                  PRIMARY KEY,
    id_usuario_autor    INT                     NOT NULL,
    id_unidade_destino  INT                     NOT NULL,
    id_categoria        INT                     NOT NULL,
    titulo              CHARACTER VARYING(150)  NOT NULL,
    descricao           TEXT                    NOT NULL,
    foto_url            CHARACTER VARYING(255)  NULL,
    video_url           CHARACTER VARYING(255)  NULL,
    prazo_sla_vigente   INTERVAL                NOT NULL,
    status              status_chamado          NOT NULL DEFAULT 'Aberto',
    data_visto          TIMESTAMP               NULL,
    data_abertura       TIMESTAMP               NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo               BOOLEAN                 NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_chamado_usuario_autor
        FOREIGN KEY (id_usuario_autor) REFERENCES usuario (id),
    CONSTRAINT fk_chamado_unidade_destino
        FOREIGN KEY (id_unidade_destino) REFERENCES unidade (id),
    CONSTRAINT fk_chamado_categoria
        FOREIGN KEY (id_categoria) REFERENCES categoria_chamado (id)
);

COMMENT ON TABLE  chamado                    IS 'Registros de atendimento (tickets) abertos pelos moradores.';
COMMENT ON COLUMN chamado.id                 IS 'Número principal do ticket de atendimento.';
COMMENT ON COLUMN chamado.id_usuario_autor   IS 'Morador responsável pela abertura do ticket.';
COMMENT ON COLUMN chamado.id_unidade_destino IS 'Unidade que apresenta a demanda/problema.';
COMMENT ON COLUMN chamado.id_categoria       IS 'Classificação técnica vinculada.';
COMMENT ON COLUMN chamado.titulo             IS 'Resumo rápido do que se trata o chamado.';
COMMENT ON COLUMN chamado.descricao          IS 'Detalhamento escrito da situação relatada.';
COMMENT ON COLUMN chamado.foto_url           IS 'Caminho/URL da foto inserida no chamado (opcional).';
COMMENT ON COLUMN chamado.video_url          IS 'Caminho/URL do vídeo inserido no chamado (opcional).';
COMMENT ON COLUMN chamado.prazo_sla_vigente  IS 'Tempo de SLA herdado da categoria no exato momento da abertura.';
COMMENT ON COLUMN chamado.status             IS 'Controle do ciclo de vida da demanda.';
COMMENT ON COLUMN chamado.data_visto         IS 'Marca temporal do primeiro acesso do síndico ao ticket.';
COMMENT ON COLUMN chamado.data_abertura      IS 'Data e hora automática do momento da criação.';
COMMENT ON COLUMN chamado.ativo              IS 'Controle para inativação (Soft Delete).';

-- ---------------------------------------------------------------------
-- 1.7 historico_chamado
-- Log de auditoria para rastrear o ciclo de vida e mudanças de status.
-- ---------------------------------------------------------------------
CREATE TABLE historico_chamado (
    id               SERIAL          PRIMARY KEY,
    id_chamado       INT             NOT NULL,
    data_alteracao   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status_anterior  status_chamado  NOT NULL,
    novo_status      status_chamado  NOT NULL,
    observacao       TEXT            NULL,

    CONSTRAINT fk_historico_chamado
        FOREIGN KEY (id_chamado) REFERENCES chamado (id)
);

COMMENT ON TABLE  historico_chamado                 IS 'Log de auditoria do ciclo de vida e mudanças de status dos chamados.';
COMMENT ON COLUMN historico_chamado.id              IS 'Identificador único da alteração de status.';
COMMENT ON COLUMN historico_chamado.id_chamado      IS 'Referência ao chamado que sofreu a ação.';
COMMENT ON COLUMN historico_chamado.data_alteracao  IS 'Data e hora automática da mudança.';
COMMENT ON COLUMN historico_chamado.status_anterior IS 'Situação antes da alteração.';
COMMENT ON COLUMN historico_chamado.novo_status     IS 'Situação para a qual o chamado foi promovido.';
COMMENT ON COLUMN historico_chamado.observacao      IS 'Campo livre para o síndico detalhar o motivo da ação.';

-- ---------------------------------------------------------------------
-- 2. Índices nas chaves estrangeiras (PostgreSQL não cria automaticamente)
-- ---------------------------------------------------------------------
CREATE INDEX idx_condominio_id_sindico          ON condominio (id_sindico);
CREATE INDEX idx_unidade_id_condominio          ON unidade (id_condominio);
CREATE INDEX idx_usuario_unidade_id_unidade     ON usuario_unidade (id_unidade);
CREATE INDEX idx_categoria_id_condominio        ON categoria_chamado (id_condominio);
CREATE INDEX idx_chamado_id_usuario_autor       ON chamado (id_usuario_autor);
CREATE INDEX idx_chamado_id_unidade_destino     ON chamado (id_unidade_destino);
CREATE INDEX idx_chamado_id_categoria           ON chamado (id_categoria);
CREATE INDEX idx_chamado_status                 ON chamado (status);
CREATE INDEX idx_historico_chamado_id_chamado   ON historico_chamado (id_chamado);

COMMIT;
