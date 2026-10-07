// Acesso à API do Zelus: toda requisição das telas passa por aqui.
// Cuida da URL base, do token JWT, do formato JSON e da tradução das mensagens de erro.
import { API_URL, ROTAS } from "./config.js";

const CHAVE_TOKEN = "zelus.token";
const CHAVE_USUARIO = "zelus.usuario";

// ==========================================
// SESSÃO (token e dados do usuário logado)
// ==========================================
export const sessao = {
    obterToken() {
        return localStorage.getItem(CHAVE_TOKEN);
    },
    obterUsuario() {
        const json = localStorage.getItem(CHAVE_USUARIO);
        return json ? JSON.parse(json) : null;
    },
    salvar(token, usuario) {
        localStorage.setItem(CHAVE_TOKEN, token);
        this.salvarUsuario(usuario);
    },
    salvarUsuario(usuario) {
        localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
    },
    limpar() {
        localStorage.removeItem(CHAVE_TOKEN);
        localStorage.removeItem(CHAVE_USUARIO);
    }
};

// ==========================================
// ERROS
// ==========================================
export class ApiError extends Error {
    constructor(status, mensagem, detalhe = null) {
        super(mensagem);
        this.name = "ApiError";
        this.status = status;   // 0 = API fora do ar / sem conexão
        this.detalhe = detalhe; // corpo "detail" original da API
    }
}

const NOMES_CAMPOS = {
    email: "E-mail",
    senha: "Senha",
    senha_atual: "Senha atual",
    nova_senha: "Nova senha",
    confirmar_nova_senha: "Confirmar nova senha",
    nome: "Nome",
    id_unidade: "Unidade",
    token: "Link"
};

// Erros 422 do FastAPI chegam como lista: [{ loc: ["body", "campo"], msg, type, ctx }]
function traduzirErroDeValidacao(erro) {
    const campo = erro.loc?.[erro.loc.length - 1];
    const nome = NOMES_CAMPOS[campo] || campo;

    switch (erro.type) {
        case "missing":
            return `${nome}: campo obrigatório.`;
        case "string_too_short":
            return `${nome}: mínimo de ${erro.ctx?.min_length} caracteres.`;
        case "string_too_long":
            return `${nome}: máximo de ${erro.ctx?.max_length} caracteres.`;
        case "value_error":
            // Validações do Pydantic (EmailStr e model_validator)
            if (campo === "email") return "Informe um e-mail válido.";
            return erro.msg.replace(/^Value error, /, "");
        default:
            return `${nome}: ${erro.msg}`;
    }
}

function extrairMensagem(status, corpo) {
    const detalhe = corpo?.detail;
    if (typeof detalhe === "string") return detalhe;
    if (Array.isArray(detalhe)) return detalhe.map(traduzirErroDeValidacao).join(" ");

    if (status === 401) return "Sessão expirada. Faça login novamente.";
    if (status === 403) return "Você não tem permissão para esta ação.";
    if (status === 404) return "Registro não encontrado.";
    return "Ocorreu um erro inesperado. Tente novamente.";
}

// ==========================================
// REQUISIÇÕES
// ==========================================
// Troca de página e deixa a requisição "pendurada", para a tela não exibir um erro durante o redirecionamento
function redirecionar(caminho) {
    window.location.replace(caminho);
    return new Promise(() => {});
}

/**
 * Faz uma requisição à API e devolve o JSON da resposta.
 * Em caso de erro, lança ApiError com a mensagem pronta para exibir ao usuário.
 *
 * @param {string} caminho  Ex.: "/auth/login"
 * @param {object} opcoes   { metodo: "GET"|"POST"|"PUT"|"PATCH"|"DELETE", corpo: objeto, autenticado: true }
 */
export async function api(caminho, { metodo = "GET", corpo = undefined, autenticado = true } = {}) {
    const cabecalhos = { "Accept": "application/json" };
    if (corpo !== undefined) cabecalhos["Content-Type"] = "application/json";

    const token = sessao.obterToken();
    if (autenticado && token) cabecalhos["Authorization"] = `Bearer ${token}`;

    let resposta;
    try {
        resposta = await fetch(API_URL + caminho, {
            method: metodo,
            headers: cabecalhos,
            body: corpo !== undefined ? JSON.stringify(corpo) : undefined
        });
    } catch {
        throw new ApiError(0, "Não foi possível conectar ao servidor. Verifique se a API está rodando.");
    }

    // Algumas respostas podem vir sem corpo
    const texto = await resposta.text();
    const dados = texto ? JSON.parse(texto) : null;

    if (resposta.ok) return dados;

    const mensagem = extrairMensagem(resposta.status, dados);

    if (autenticado) {
        // Token ausente, expirado ou usuário inativado: volta ao login
        if (resposta.status === 401) {
            sessao.limpar();
            return redirecionar(`${ROTAS.login}?motivo=sessao`);
        }
        // RN13: senha provisória ainda não trocada
        if (resposta.status === 403 && mensagem.includes("senha provisória")) {
            return redirecionar(ROTAS.trocarSenha);
        }
    }

    throw new ApiError(resposta.status, mensagem, dados?.detail);
}
