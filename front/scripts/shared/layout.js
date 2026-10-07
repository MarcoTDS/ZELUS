// Cabeçalho (navbar) das telas logadas. Uso: montarCabecalho(usuario) depois do protegerPagina().
// A tela precisa ter <header id="cabecalho"></header> no início do <body>.
import { rotaInicial, sair } from "./auth-guard.js";
import { escaparHtml } from "./ui.js";

const NOMES_PERFIL = {
    Administrador: "Administrador",
    Sindico: "Síndico",
    Morador: "Morador"
};

export function montarCabecalho(usuario) {
    const cabecalho = document.getElementById("cabecalho");
    cabecalho.innerHTML = `
        <nav class="navbar navbar-expand bg-white border-bottom">
            <div class="container pagina">
                <a class="navbar-brand marca" href="${rotaInicial(usuario)}">Zelus</a>
                <div class="d-flex align-items-center gap-3">
                    <span class="small text-end lh-sm">
                        <span class="d-block fw-semibold">${escaparHtml(usuario.nome)}</span>
                        <span class="texto-suave">${NOMES_PERFIL[usuario.perfil] || usuario.perfil}</span>
                    </span>
                    <button type="button" id="btn-sair" class="btn btn-outline-secondary btn-sm">Sair</button>
                </div>
            </div>
        </nav>
    `;
    document.getElementById("btn-sair").addEventListener("click", sair);
}
