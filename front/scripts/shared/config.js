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

    // Administrador
    admin: {
        condominio: "/views/admin/condominio.html",
        cadastroSindico: "/views/admin/cadastro-sindico.html"
    },

    // Dashboard de cada perfil (RF02, RF03, RF04)
    inicio: {
        Morador: "/views/morador/dashboard.html",
        Sindico: "/views/sindico/dashboard.html",
        Administrador: "/views/admin/dashboard.html"
    }
};
