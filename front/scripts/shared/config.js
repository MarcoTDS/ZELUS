// Configurações compartilhadas por todas as telas do Zelus.

// Endereço da API (uvicorn). Em produção, troque pelo domínio do servidor.
export const API_URL = "http://127.0.0.1:8000";

// API pública de consulta de CEP (preenchimento do endereço do condomínio)
export const VIACEP_URL = "https://viacep.com.br/ws";
 
// Caminhos das telas, a partir da pasta front/ (raiz do servidor).
export const ROTAS = {
    login: "/views/auth/login.html",
    cadastro: "/views/auth/cadastro.html",
    trocarSenha: "/views/auth/trocar-senha.html",
 
    // Dashboard de cada perfil
    inicio: {
        Morador: "/views/morador/dashboard.html",
        Sindico: "/views/sindico/dashboard.html",
        Administrador: "/views/admin/dashboard.html"
    },
 
    // Administrador
    admin: {
        condominio: "/views/admin/cadastro-condominio.html",
        cadastroSindico: "/views/admin/cadastro-sindico.html"
    },
 
    // Síndico
    sindico: {
        worklist: "/views/sindico/worklist.html",
        categorias: "/views/sindico/categorias.html",
        cadastrosPendentes: "/views/sindico/cadastros-pendentes.html"
    },
 
    // Morador
    morador: {
        novoChamado: "/views/morador/novo-chamado.html"
    },
 
    // Telas compartilhadas entre perfis
    comum: {
        chamado: "/views/comum/chamado.html"      // abre com ?id=N
    }
 
    // Fora da pré-banca (voltam aqui quando as telas forem refeitas):
    // esqueciSenha, sindico.historico, sindico.moradores, sindico.unidades,
    // comum.mural, comum.perfil, comum.alterarSenha
};
 
// ==========================================
// MENU DA NAVBAR POR PERFIL
// ==========================================
// Cada item é um link { texto, icone, rota } ou um grupo { texto, icone, itens: [...] }.
// Ícones: nomes do Bootstrap Icons (https://icons.getbootstrap.com).
// ==========================================
// MENU DE LINKS NO CABEÇALHO (opcional)
// ==========================================
// Na pré-banca o cabeçalho não mostra links: só logo, usuário e tema.
// Para exibir links ao lado da logo, preencha a lista do perfil. Cada item é
// { texto, icone, rota } ou um grupo { texto, icone, itens: [...] }.
// Ícones: nomes do Bootstrap Icons (https://icons.getbootstrap.com).
// Exemplo:
//   Sindico: [
//       { texto: "Início", icone: "bi-house", rota: ROTAS.inicio.Sindico },
//       { texto: "Fila de chamados", icone: "bi-list-task", rota: ROTAS.sindico.worklist }
//   ]
export const MENUS = {
    Administrador: [],
    Sindico: [],
    Morador: []
};

// Itens do menu do usuário (lado direito da navbar), comuns ou por perfil
export const MENU_USUARIO = [
    { texto: "Editar perfil", icone: "bi-person", rota: ROTAS.comum.perfil, perfis: ["Morador"] }, // RF15
    { texto: "Alterar senha", icone: "bi-key", rota: ROTAS.comum.alterarSenha }                    // RF16
];
