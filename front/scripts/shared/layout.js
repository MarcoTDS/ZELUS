// Cabeçalho (navbar) das telas logadas, com o menu do perfil do usuário e o botão de tema.
// Uso: montarCabecalho(usuario) depois do protegerPagina().
// A tela precisa ter <header id="cabecalho"></header> no início do <body>.
//
// Os itens de cada perfil ficam em MENUS e MENU_USUARIO (config.js).
// O abrir/fechar (menu do celular e submenus) é feito aqui mesmo,
// sem depender do JavaScript do Bootstrap.
import { MENUS, MENU_USUARIO } from "./config.js";
import { rotaInicial, sair } from "./auth-guard.js";
import { escaparHtml } from "./ui.js";

const NOMES_PERFIL = {
    Administrador: "Administrador",
    Sindico: "Síndico",
    Morador: "Morador"
};

const paginaAtual = window.location.pathname;

// Logo animada (mesma do login, menor)
const LOGO = `
    <div class="logo-zelus logo-zelus-md">
        <svg class="figura-zelus" viewBox="0 0 400 400" role="img" aria-label="Logo Zelus: engrenagem entre ferramentas">
            <g class="ferramentas-zelus">
                <path d="M 128 128 L 102 102 M 102 102 L 83 108 L 60 77 L 72 65 L 104 87 Z"/>
                <path d="M 254 113 C 246 87, 265 60, 291 59 C 305 57, 307 62, 297 72 L 283 86 C 274 97, 280 110, 289 117 C 299 126, 311 126, 321 116 L 335 102 C 344 92, 348 98, 345 111 C 341 138, 319 155, 289 149"/>
                <path d="M 286 247 L 336 297 Q 346 307, 336 317 L 318 335 Q 308 345, 298 335 L 248 285"/>
                <path d="M 113 254 C 87 246, 60 265, 59 291 C 57 305, 62 307, 72 297 L 86 283 C 97 274, 110 280, 117 289 C 126 299, 126 311, 116 321 L 102 335 C 92 344, 98 348, 111 345 C 138 341, 155 319, 149 289"/>
            </g>
            <g class="engrenagem-zelus">
                <path d="M 184 112 L 216 112 L 216 133 L 237 142 L 252 127 L 275 150 L 260 165 L 269 184 L 290 184 L 290 216 L 269 216 L 260 237 L 275 252 L 252 275 L 237 260 L 216 269 L 216 290 L 184 290 L 184 269 L 163 260 L 148 275 L 125 252 L 140 237 L 131 216 L 110 216 L 110 184 L 131 184 L 140 165 L 125 150 L 148 127 L 163 142 L 184 133 Z"/>
                <circle cx="200" cy="200" r="39"/>
            </g>
        </svg>
    </div>`;

// Botão de alternar tema (o clique é tratado pelo tema.js)
const BOTAO_TEMA = `
    <button type="button" id="btnTema" class="btn btn-outline-secondary btn-tema" aria-label="Mudar para modo escuro">
        <svg class="icone-lua" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        <svg class="icone-sol d-none" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"/>
            <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
            <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
    </button>`;

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
            <button type="button" class="btn btn-link nav-link dropdown-toggle text-end lh-sm"
                    data-alternar="submenu" aria-expanded="false" id="btn-usuario">
                <span>
                    <span class="d-block fw-semibold">${escaparHtml(usuario.nome)}</span>
                    <span class="d-block small texto-suave">${NOMES_PERFIL[usuario.perfil] || usuario.perfil}</span>
                </span>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                ${itens}
                ${itens ? '<li><hr class="dropdown-divider"></li>' : ""}
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

    // Menu de links é opcional: por padrão o cabeçalho tem só logo, usuário e tema
    // (a navegação é feita pelos atalhos de cada dashboard).
    const menuLinks = itens ? `
        <ul class="navbar-nav flex-row gap-3 me-auto ms-4 d-none d-md-flex">${itens}</ul>` : "";

    cabecalho.innerHTML = `
        <nav class="zelus-topo">
            <div class="container pagina-larga d-flex align-items-center justify-content-between py-2">
                <a href="${rotaInicial(usuario)}" class="d-flex align-items-center gap-2 text-decoration-none text-reset">
                    ${LOGO}
                    <span class="fw-semibold fs-4">Zelus</span>
                </a>
                ${menuLinks}
                <div class="d-flex align-items-center gap-3">
                    ${montarMenuUsuario(usuario)}
                    ${BOTAO_TEMA}
                </div>
            </div>
        </nav>
    `;

    ativarInteracoes(cabecalho);
}