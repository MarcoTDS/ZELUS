// Cabeçalho (navbar) das telas logadas, com o menu do perfil do usuário.
// Uso: montarCabecalho(usuario) depois do protegerPagina().
// A tela precisa ter <header id="cabecalho"></header> no início do <body>.
//
// Os itens de cada perfil ficam em MENUS e MENU_USUARIO (config.js).
// O comportamento de abrir/fechar (menu no celular e submenus) é feito aqui mesmo,
// sem precisar carregar o JavaScript do Bootstrap.
import { MENUS, MENU_USUARIO } from "./config.js";
import { rotaInicial, sair } from "./auth-guard.js";
import { escaparHtml } from "./ui.js";

const NOMES_PERFIL = {
    Administrador: "Administrador",
    Sindico: "Síndico",
    Morador: "Morador"
};

const paginaAtual = window.location.pathname;

function icone(nome) {
    return nome ? `<i class="bi ${nome}" aria-hidden="true"></i> ` : "";
}

// Atributos do link da página aberta no momento
function marcarAtivo(rota) {
    return rota === paginaAtual ? ` active" aria-current="page` : "";
}

function montarLink(item) {
    return `
        <li class="nav-item">
            <a class="nav-link${marcarAtivo(item.rota)}" href="${item.rota}">${icone(item.icone)}${item.texto}</a>
        </li>`;
}

function montarGrupo(item) {
    const grupoAtivo = item.itens.some((filho) => filho.rota === paginaAtual);
    const filhos = item.itens.map((filho) => `
        <li><a class="dropdown-item${marcarAtivo(filho.rota)}" href="${filho.rota}">${icone(filho.icone)}${filho.texto}</a></li>
    `).join("");

    return `
        <li class="nav-item dropdown">
            <button type="button" class="nav-link dropdown-toggle${grupoAtivo ? " active" : ""}"
                    data-alternar="submenu" aria-expanded="false">${icone(item.icone)}${item.texto}</button>
            <ul class="dropdown-menu">${filhos}</ul>
        </li>`;
}

function montarMenuUsuario(usuario) {
    const itens = MENU_USUARIO
        .filter((item) => !item.perfis || item.perfis.includes(usuario.perfil))
        .map((item) => `<li><a class="dropdown-item${marcarAtivo(item.rota)}" href="${item.rota}">${icone(item.icone)}${item.texto}</a></li>`)
        .join("");

    return `
        <div class="dropdown menu-usuario">
            <button type="button" class="btn btn-link nav-link dropdown-toggle text-start lh-sm"
                    data-alternar="submenu" aria-expanded="false" id="btn-usuario">
                <span>
                    <span class="d-block fw-semibold">${escaparHtml(usuario.nome)}</span>
                    <span class="d-block small texto-suave">${NOMES_PERFIL[usuario.perfil] || usuario.perfil}</span>
                </span>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                ${itens}
                <li><hr class="dropdown-divider"></li>
                <li><button type="button" class="dropdown-item text-danger" id="btn-sair">${icone("bi-box-arrow-right")}Sair</button></li>
            </ul>
        </div>`;
}

// ==========================================
// ABRIR E FECHAR (menu do celular e submenus)
// ==========================================
function fecharSubmenus(exceto = null) {
    document.querySelectorAll("#cabecalho [data-alternar='submenu']").forEach((botao) => {
        if (botao === exceto) return;
        botao.setAttribute("aria-expanded", "false");
        botao.nextElementSibling.classList.remove("show");
    });
}

function ativarInteracoes(cabecalho) {
    cabecalho.addEventListener("click", (evento) => {
        const botao = evento.target.closest("[data-alternar]");
        if (!botao) return;

        if (botao.dataset.alternar === "menu") {
            // Botão "hambúrguer" (telas pequenas)
            const menu = document.getElementById("menu-principal");
            const aberto = menu.classList.toggle("show");
            botao.setAttribute("aria-expanded", String(aberto));
            return;
        }

        // Submenu (grupo do menu ou menu do usuário)
        const lista = botao.nextElementSibling;
        const abrir = !lista.classList.contains("show");
        fecharSubmenus(botao);
        lista.classList.toggle("show", abrir);
        botao.setAttribute("aria-expanded", String(abrir));
    });

    // Clicar fora ou apertar Esc fecha os submenus
    document.addEventListener("click", (evento) => {
        if (!evento.target.closest("#cabecalho .dropdown")) fecharSubmenus();
    });
    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") fecharSubmenus();
    });

    document.getElementById("btn-sair").addEventListener("click", sair);
}

// ==========================================
// MONTAGEM
// ==========================================
export function montarCabecalho(usuario) {
    const cabecalho = document.getElementById("cabecalho");
    const itens = (MENUS[usuario.perfil] || [])
        .map((item) => item.itens ? montarGrupo(item) : montarLink(item))
        .join("");

    cabecalho.innerHTML = `
        <nav class="navbar navbar-expand-lg bg-white border-bottom">
            <div class="container pagina-larga">
                <a class="navbar-brand marca" href="${rotaInicial(usuario)}">Zelus</a>

                <button class="navbar-toggler" type="button" data-alternar="menu"
                        aria-controls="menu-principal" aria-expanded="false" aria-label="Abrir menu">
                    <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="menu-principal">
                    <ul class="navbar-nav me-auto">${itens}</ul>
                    ${montarMenuUsuario(usuario)}
                </div>
            </div>
        </nav>
    `;

    ativarInteracoes(cabecalho);
}
