[README.md](https://github.com/user-attachments/files/34034067/README.md)
# Zelus — Help Desk para Manutenção Condominial

Plataforma web para abrir, priorizar e acompanhar chamados de manutenção corretiva em condomínios residenciais. O morador registra o problema (com foto e vídeo), o sistema calcula o prazo de atendimento (SLA) pela categoria e o síndico trabalha numa fila ordenada por urgência, com histórico de cada mudança de status.

**Acesse:** [https://zelus.api.br](https://zelus.api.br)

Projeto Integrador do curso de Tecnologia em Análise e Desenvolvimento de Sistemas (IFPR).

**Equipe:** Karen Gabriela Neres e Marco Aurélio Dias Souza

---

## Sumário

- [Por que o Zelus](#por-que-o-zelus)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Arquitetura e estrutura de pastas](#arquitetura-e-estrutura-de-pastas)
- [Como rodar localmente](#como-rodar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Endpoints da API](#endpoints-da-api)
- [Regras de negócio principais](#regras-de-negócio-principais)
- [Deploy](#deploy)
- [Documentação do projeto](#documentação-do-projeto)

---

## Por que o Zelus

Em muitos condomínios, problemas de infraestrutura ainda são comunicados por aplicativos de mensagem ou de forma verbal. Isso causa perda de informação, falta de rastreabilidade e nenhuma priorização: um vazamento grave pode esperar atrás de um pedido simples só porque chegou depois.

Ferramentas como Zendesk, GLPI e Jira Service Management resolvem esse problema no mundo corporativo, mas são complexas demais para a escala de um condomínio. O Zelus é uma solução enxuta e focada nessa realidade.

## Funcionalidades

O sistema tem três perfis de acesso.

### Morador
- Cadastro com nome, e-mail e senha, escolhendo o condomínio e uma ou mais unidades (o acesso fica pendente até a aprovação do síndico).
- Abertura de chamado com título, descrição, categoria, unidade e anexo opcional de **1 foto** (JPG, PNG ou WEBP, até 5 MB) e **1 vídeo** (MP4, MOV ou WEBM, até 50 MB).
- Aviso de chamado semelhante já aberto (mesma categoria e unidade), sem bloquear a abertura.
- Lista dos próprios chamados e **mural** público do condomínio (somente leitura), com busca por número do ticket.
- Detalhes do chamado com histórico de status e marcador "Visto" pelo síndico.
- Gestão das próprias unidades, edição de perfil e troca de senha.

### Síndico
- Dashboard com o resumo do condomínio: chamados abertos, urgentes e vencidos.
- **Worklist**: fila de chamados ordenada pela urgência do SLA, com cores por proximidade do prazo e rótulo **"Vencido"** quando o prazo expira.
- Alteração de status (Aberto → Em Andamento → Resolvido, ou Cancelado), sempre com observação registrada no histórico.
- Cadastro, edição e inativação de **categorias** com prazo de SLA em horas ou dias.
- Aprovação ou rejeição de **cadastros pendentes**, com aviso quando a unidade já tem responsável.
- Gestão de **moradores** e **unidades** do condomínio.
- Histórico completo de chamados, incluindo resolvidos e cancelados.
- Senha provisória obrigatoriamente trocada no primeiro acesso.

### Administrador
- Cadastro, edição, inativação e reativação de **condomínios** (endereço preenchido pelo CEP via ViaCEP) e de suas unidades.
- Cadastro do **síndico** de cada condomínio: o sistema gera a senha provisória e envia o link de validação de e-mail.
- Desvinculação de síndico e inativação/reativação de usuários.

### Para todos
- Login com e-mail e senha (JWT), recuperação de senha por e-mail e interface responsiva (desktop e celular), com tema claro e escuro.

## Tecnologias

| Camada | Tecnologias |
|---|---|
| Back-end | Python, [FastAPI](https://fastapi.tiangolo.com/), Uvicorn, SQLAlchemy, Pydantic, PyJWT (HS256), bcrypt, python-dotenv, python-multipart |
| Banco de dados | PostgreSQL (driver psycopg2) |
| Front-end | HTML, CSS e JavaScript puro (ES Modules), Bootstrap e Bootstrap Icons via CDN, Fetch API |
| Serviços externos | ViaCEP (consulta de CEP), SMTP (envio de e-mails via `smtplib`) |
| Ferramentas | Git e GitHub, VS Code com Live Server, Swagger UI (documentação automática da API) |

## Arquitetura e estrutura de pastas

A arquitetura é desacoplada: o front-end estático consome uma API REST. O back-end é organizado em camadas.

```
ZELUS/
├── main.py              # cria a aplicação FastAPI, CORS e registra as rotas
├── database.py          # conexão com o PostgreSQL (SQLAlchemy)
├── requirements.txt
├── .env.example         # modelo das variáveis de ambiente
├── models/              # tabelas do banco (SQLAlchemy)
├── schemas/             # validação de entrada e saída (Pydantic)
├── routers/             # rotas (controllers) da API
├── service/             # regras de negócio (chamados, anexos, e-mail, autenticação...)
└── front/               # front-end estático
    ├── index.html       # redireciona para o login ou para o dashboard do perfil
    ├── styles/          # CSS global
    ├── scripts/
    │   ├── shared/      # config da API, fetch com token, guarda de rotas, layout, tema
    │   ├── auth/        # login, cadastro, validação de e-mail, senhas
    │   ├── admin/
    │   ├── sindico/
    │   ├── morador/
    │   └── comum/       # telas usadas por mais de um perfil (detalhe do chamado, perfil)
    └── views/           # páginas HTML, separadas por perfil (mesma divisão dos scripts)
```

## Como rodar localmente

### Pré-requisitos
- Python 3.10 ou superior
- PostgreSQL 14 ou superior
- VS Code com a extensão **Live Server** (ou qualquer servidor de arquivos estáticos)

### 1. Clonar e instalar as dependências

```bash
git clone https://github.com/MarcoTDS/ZELUS.git
cd ZELUS
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Criar o banco

```sql
CREATE USER zelus WITH PASSWORD 'SENHA_DO_BANCO';
CREATE DATABASE zelus OWNER zelus;
```

As tabelas são criadas automaticamente pela API na primeira inicialização (`Base.metadata.create_all` em `main.py`).

### 3. Configurar o `.env`

```bash
cp .env.example .env
```

Preencha pelo menos `ZELUS_SECRET_KEY` e `ZELUS_DATABASE_URL` (veja a [tabela abaixo](#variáveis-de-ambiente)). Para gerar a chave do JWT:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> Sem `ZELUS_SMTP_HOST`, os e-mails (validação e redefinição de senha) não são enviados: o conteúdo aparece no terminal do Uvicorn, o que é suficiente para testar.

### 4. Subir a API

```bash
uvicorn main:app --reload
```

A API fica em `http://127.0.0.1:8000` e a documentação interativa (Swagger) em `http://127.0.0.1:8000/docs`.

### 5. Criar o primeiro administrador

O banco começa vazio e o administrador não tem tela de cadastro. Salve o script abaixo como `criar_admin.py` na raiz do projeto (ele já está no `.gitignore`) e rode `python criar_admin.py`:

```python
from getpass import getpass
from dotenv import load_dotenv
load_dotenv()
import main  # registra os modelos
from database import SessionLocal
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum
from service.usuario_service import obter_hash_senha

nome = input("Nome: ")
email = input("E-mail: ").strip().lower()
senha = getpass("Senha: ")
db = SessionLocal()
db.add(UsuarioDB(nome=nome, email=email, senha=obter_hash_senha(senha),
                 perfil=PerfilUsuarioEnum.Administrador,
                 email_validado=True, senha_provisoria=False, ativo=True))
db.commit()
print("Administrador criado.")
```

### 6. Abrir o front-end

No VS Code, clique em **Go Live**. O `.vscode/settings.json` já configura o Live Server para servir a pasta `front/` na porta **5501**:

```
http://127.0.0.1:5501/views/auth/login.html
```

Rodando em `localhost`/`127.0.0.1`, o front chama a API em `http://127.0.0.1:8000`; em produção, chama `/api` no mesmo domínio (ver `front/scripts/shared/config.js`).

### Fluxo para testar
1. Entre como **administrador**, cadastre um condomínio com unidades e o síndico.
2. Valide o e-mail do síndico pelo link (no e-mail ou no terminal) e entre com a senha provisória, que deverá ser trocada.
3. Como **síndico**, cadastre as categorias e seus prazos de SLA.
4. Cadastre-se como **morador** na tela de cadastro e aprove a solicitação pelo síndico.
5. Abra chamados como morador e acompanhe-os pela worklist do síndico.

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `ZELUS_SECRET_KEY` | Sim | Chave de assinatura dos tokens JWT |
| `ZELUS_DATABASE_URL` | Sim | URL do PostgreSQL, ex.: `postgresql://zelus:SENHA@localhost:5432/zelus` |
| `ZELUS_URL_FRONTEND` | Não | Endereço do front usado nos links dos e-mails, sem barra final (padrão `http://127.0.0.1:5501`) |
| `ZELUS_CORS_ORIGINS` | Não | Origens extras liberadas no CORS, separadas por vírgula (ex.: o domínio de produção) |
| `ZELUS_UPLOADS_DIR` | Não | Pasta onde as fotos e vídeos dos chamados são gravados (padrão `uploads`) |
| `ZELUS_SMTP_HOST` | Não | Servidor SMTP; sem ele, os e-mails só aparecem no terminal |
| `ZELUS_SMTP_PORTA` | Não | Porta SMTP (padrão `587`) |
| `ZELUS_SMTP_TLS` | Não | Usa STARTTLS (padrão `true`) |
| `ZELUS_SMTP_USUARIO` / `ZELUS_SMTP_SENHA` | Não | Credenciais do SMTP. No Gmail, use uma [senha de app](https://myaccount.google.com/apppasswords) |
| `ZELUS_SMTP_REMETENTE` | Não | Remetente dos e-mails (padrão: o usuário SMTP) |

> Nunca versione o arquivo `.env` com valores reais.

## Endpoints da API

A lista completa, com os esquemas de entrada e saída, está no Swagger (`/docs`). Resumo por grupo:

| Grupo | Principais rotas |
|---|---|
| Autenticação | `POST /login`, `POST /cadastro`, `POST /validar-email`, `POST /esqueci-senha`, `POST /redefinir-senha`, `GET/PATCH /me`, `PATCH /me/senha`, `GET /me/unidades` |
| Público (cadastro) | condomínios disponíveis e suas unidades |
| Administrador | CRUD de condomínios e unidades, inativar/reativar condomínio, cadastro de síndico, reenvio do link de validação, desvincular síndico, inativar/reativar usuário |
| Chamados | abrir chamado, verificar semelhança, meus chamados, mural, worklist, histórico, resumo do dashboard, alterar status, detalhes, histórico de status, envio e visualização de foto/vídeo |
| Vínculos | solicitar unidade, minhas unidades, sair da unidade, cadastros pendentes, aprovar/rejeitar |
| Moradores | listar, editar, inativar/reativar, remover da unidade |
| Unidades | listar, cadastrar, editar, inativar (síndico), unidades disponíveis para chamado |
| Categorias | listar, cadastrar, editar, inativar |

## Regras de negócio principais

- **SLA:** o prazo do chamado é fixado na abertura, com base no prazo vigente da categoria escolhida.
- **Status:** só o síndico altera o status ou cancela um chamado; chamados Resolvidos ou Cancelados não mudam mais. Toda mudança gera um registro no histórico (data, status anterior, novo status e observação).
- **Urgência visual:** a cor do chamado indica a proximidade do vencimento; prazo expirado com o chamado Aberto ou Em Andamento exibe "Vencido".
- **Mural:** o morador vê todos os chamados do condomínio, mas só gerencia os das próprias unidades.
- **Isolamento:** cada condomínio tem exatamente um síndico, que só acessa os dados do próprio condomínio.
- **Exclusão lógica:** nada é apagado fisicamente; remoções são feitas por inativação, preservando o histórico para auditoria.
- **Segurança:** senhas com hash bcrypt; tokens de validação de e-mail (2 dias) e de redefinição de senha (1 hora) são de uso único, e só o hash SHA-256 deles é salvo; anexos são validados pelo conteúdo do arquivo e servidos por link temporário.

A especificação completa (RF01–RF22, RNF01–RNF06 e RN01–RN17) está no documento de requisitos.

## Deploy

O Zelus está no ar em **[https://zelus.api.br](https://zelus.api.br)**.

Em produção, ele roda numa VPS Ubuntu com:

- **Nginx** servindo a pasta `front/` e repassando `/api` para a API;
- **Uvicorn** como serviço do **systemd**;
- **PostgreSQL** local;
- **HTTPS** com Let's Encrypt (Certbot).

## Documentação do projeto

- Termo de abertura
- Especificação de requisitos e regras de negócio
- Prototipação das telas
- Dicionário de dados
