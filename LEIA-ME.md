# Zelus front-end: base + login (entrega 1)

Copie o conteúdo desta pasta para a raiz do repositório (ao lado de `main.py`):

```
.vscode/settings.json            → Live Server servindo a pasta front/ na porta 5500
front/
├── index.html                   → redireciona para o dashboard (se logado) ou para o login
├── styles/global.css            → cores da marca, cartão das telas de autenticação
├── scripts/shared/
│   ├── config.js                → URL da API e caminhos das telas
│   ├── api.js                   → fetch, token JWT, mensagens de erro em português
│   ├── auth-guard.js            → protegerPagina(), rotaInicial(), sair()
│   └── ui.js                    → alertas e botão com "carregando"
├── views/auth/login.html        + scripts/auth/login.js         (1.1, RF01)
└── views/auth/trocar-senha.html + scripts/auth/trocar-senha.js  (1.17, RF16/RN13)
```

## Como rodar
1. API: `uvicorn main:app --reload` (porta 8000).
2. VS Code: "Go Live". Com o `.vscode/settings.json`, o Live Server abre a pasta `front/` como raiz, então o login fica em `http://127.0.0.1:5500/views/auth/login.html`.
   Se preferir não usar o settings.json, clique com o botão direito em `front/` e use o Live Server a partir dela.

## Como uma tela nova usa a base
```html
<body data-protegida>   <!-- fica oculta até o login ser confirmado -->
...
<script type="module" src="../../scripts/sindico/worklist.js"></script>
```
```js
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
const chamados = await api("/chamados/worklist?status=Aberto");
await api(`/chamados/${id}/status`, { metodo: "PATCH", corpo: { novo_status: "Em Andamento" } });
```
- `api()` já envia o token, converte o JSON e lança `ApiError` com `erro.message` pronta para exibir.
- 401 (sessão expirada / usuário inativado) → volta ao login com aviso.
- 403 de senha provisória → vai para a troca de senha.
- Erros 422 do FastAPI são traduzidos (campo obrigatório, mínimo de caracteres, e-mail inválido).

## Ajuste na API (links dos e-mails)
Com as telas em `front/views/auth/`, os links gerados pela API precisam do caminho novo:

`service/admin_service.py`, linha 133:
```python
    link_validacao = f"{URL_FRONTEND}/views/auth/validar-email.html?token={token}"
```

`service/usuario_service.py`, linha 151:
```python
        f"{URL_FRONTEND}/views/auth/redefinir-senha.html?token={token}"
```

## Testado
API rodando contra um PostgreSQL 16 com o seu `zelus_schema.sql` + `zelus_migracao_v3_para_v4.sql`, e as telas abertas no Chromium (Playwright):
- sem login, abrir a troca de senha → login
- campos vazios → validação do Bootstrap, sem chamar a API
- senha errada → "E-mail ou senha incorretos."
- morador pendente → aviso de pendência, sem entrar
- síndico com senha provisória → troca de senha; confirmação diferente bloqueada; provisória errada → "A senha atual informada está incorreta."; senha correta → dashboard do síndico
- após trocar, voltar à troca de senha → dashboard
- token inválido → login com "Sua sessão expirou"
- admin → dashboard do admin
- nenhum erro no console

Os dashboards (`views/morador|sindico|admin/dashboard.html`) ainda não existem, então o redirecionamento final cai num 404 até eles serem criados.
