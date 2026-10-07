// Proteção das telas que exigem login.
// Uso no script de cada tela:  const usuario = await protegerPagina({ perfis: ["Sindico"] });
import { ROTAS } from "./config.js";
import { api, sessao } from "./api.js";

// Tela inicial de acordo com a situação do usuário (RN13 e perfil)
export function rotaInicial(usuario) {
    if (usuario.senha_provisoria) return ROTAS.trocarSenha;
    return ROTAS.inicio[usuario.perfil] || ROTAS.login;
}

function redirecionar(caminho) {
    window.location.replace(caminho);
    // Interrompe o script da tela enquanto o navegador troca de página
    return new Promise(() => {});
}

/**
 * Confere o login antes de exibir a tela e devolve os dados do usuário (GET /auth/me).
 *
 * @param {object} opcoes
 * @param {string[]} opcoes.perfis                  Perfis que podem abrir a tela (vazio = qualquer perfil)
 * @param {boolean}  opcoes.permitirSenhaProvisoria  true apenas na tela de troca de senha do 1º acesso
 */
export async function protegerPagina({ perfis = [], permitirSenhaProvisoria = false } = {}) {
    if (!sessao.obterToken()) return redirecionar(ROTAS.login);

    // Sempre consulta a API: inativações e aprovações têm efeito imediato
    const usuario = await api("/auth/me");
    sessao.salvarUsuario(usuario);

    if (usuario.senha_provisoria && !permitirSenhaProvisoria) {
        return redirecionar(ROTAS.trocarSenha);
    }

    // Morador com cadastro pendente ou rejeitado não acessa o sistema
    if (usuario.perfil === "Morador" && usuario.status_vinculo !== "Aprovado") {
        sessao.limpar();
        return redirecionar(`${ROTAS.login}?motivo=pendente`);
    }

    if (perfis.length && !perfis.includes(usuario.perfil)) {
        return redirecionar(rotaInicial(usuario));
    }

    // Libera a exibição da tela (veja body[data-protegida] no global.css)
    document.body.removeAttribute("data-protegida");
    return usuario;
}

export function sair() {
    sessao.limpar();
    window.location.replace(ROTAS.login);
}
