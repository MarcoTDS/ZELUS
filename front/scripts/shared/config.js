// Configurações compartilhadas por todas as telas do Zelus.

// Endereço da API (uvicorn). Em produção, troque pelo domínio do servidor.
export const API_URL = "http://127.0.0.1:8000";

// API pública de consulta de CEP (preenchimento do endereço do condomínio)
export const VIACEP_URL = "https://viacep.com.br/ws";

// Caminhos das telas, a partir da pasta front/ (raiz do Live Server).
export const ROTAS = {
    login: "/views/auth/login.html",
    esqueciSenha: "/views/auth/esqueci-senha.html",
    cadastro: "/views/auth/cadastro.html",
    trocarSenha: "/views/auth/trocar-senha.html",

    // Dashboard de cada perfil (RF02, RF03, RF04)
    inicio: {
        Morador: "/views/morador/dashboard.html",
        Sindico: "/views/sindico/dashboard.html",
        Administrador: "/views/admin/dashboard.html"
    },

    // Administrador
    admin: {
        condominio: "/views/admin/condominio.html",              // 1.20
        cadastroSindico: "/views/admin/cadastro-sindico.html"    // 1.21
    },

    // Síndico
    sindico: {
        worklist: "/views/sindico/worklist.html",                // 1.10
        historico: "/views/sindico/historico.html",              // 1.16
        categorias: "/views/sindico/categorias.html",            // 1.12
        cadastrosPendentes: "/views/sindico/cadastros-pendentes.html", // 1.13
        moradores: "/views/sindico/moradores.html",              // 1.14
        unidades: "/views/sindico/unidades.html"                 // 1.15
    },

    // Morador
    morador: {
        novoChamado: "/views/morador/novo-chamado.html"          // 1.5
    },

    // Telas compartilhadas entre perfis
    comum: {
        chamado: "/views/comum/chamado.html",                    // 1.6 / 1.11 (?id=N)
        mural: "/views/comum/mural.html",                        // 1.7
        perfil: "/views/comum/perfil.html",                      // 1.8
        alterarSenha: "/views/comum/alterar-senha.html"          // 1.18
    }
};

// ==========================================
// MENU DA NAVBAR POR PERFIL
// ==========================================
// Cada item é um link { texto, icone, rota } ou um grupo { texto, icone, itens: [...] } (submenu).
// Ícones: nomes do Bootstrap Icons (https://icons.getbootstrap.com).
export const MENUS = {
    Administrador: [
        { texto: "Condomínios", icone: "bi-buildings", rota: ROTAS.inicio.Administrador },
        { texto: "Cadastrar condomínio", icone: "bi-building-add", rota: ROTAS.admin.condominio },
        { texto: "Cadastrar síndico", icone: "bi-person-plus", rota: ROTAS.admin.cadastroSindico }
    ],

    Sindico: [
        { texto: "Início", icone: "bi-house", rota: ROTAS.inicio.Sindico },
        {
            texto: "Chamados", icone: "bi-tools", itens: [
                { texto: "Fila de chamados", icone: "bi-list-task", rota: ROTAS.sindico.worklist },
                { texto: "Histórico", icone: "bi-clock-history", rota: ROTAS.sindico.historico },
                { texto: "Mural do condomínio", icone: "bi-megaphone", rota: ROTAS.comum.mural }
            ]
        },
        {
            texto: "Gestão", icone: "bi-gear", itens: [
                { texto: "Cadastros pendentes", icone: "bi-person-check", rota: ROTAS.sindico.cadastrosPendentes },
                { texto: "Moradores", icone: "bi-people", rota: ROTAS.sindico.moradores },
                { texto: "Unidades", icone: "bi-door-closed", rota: ROTAS.sindico.unidades },
                { texto: "Categorias e SLA", icone: "bi-tags", rota: ROTAS.sindico.categorias }
            ]
        }
    ],

    Morador: [
        { texto: "Meus chamados", icone: "bi-house", rota: ROTAS.inicio.Morador },
        { texto: "Novo chamado", icone: "bi-plus-circle", rota: ROTAS.morador.novoChamado },
        { texto: "Mural", icone: "bi-megaphone", rota: ROTAS.comum.mural }
    ]
};

// Itens do menu do usuário (lado direito da navbar), comuns ou por perfil
export const MENU_USUARIO = [
    { texto: "Editar perfil", icone: "bi-person", rota: ROTAS.comum.perfil, perfis: ["Morador"] }, // RF15
    { texto: "Alterar senha", icone: "bi-key", rota: ROTAS.comum.alterarSenha }                    // RF16
];
