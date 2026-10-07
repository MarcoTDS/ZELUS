// 1.19 Tela Dashboard do Perfil Administrador (RF04, RN12, RN15)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, mostrarAvisoPendente, escaparHtml, definirCarregando } from "../shared/ui.js";
import { mostrarAcessoSindico } from "./acesso-sindico.js";

const usuario = await protegerPagina({ perfis: ["Administrador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-condominios");
const mostrarInativos = document.getElementById("mostrar-inativos");
const acessoSindico = document.getElementById("acesso-sindico");

mostrarAvisoPendente(alerta);

function textoSindico(condominio) {
    if (!condominio.sindico) {
        return `<span class="text-warning-emphasis">Sem síndico</span> ·
                <a href="cadastro-sindico.html?condominio=${condominio.id}">Cadastrar síndico</a>`;
    }
    const pendente = condominio.sindico.email_validado ? "" :
        ` <span class="badge text-bg-warning">E-mail não validado</span>`;
    return `Síndico: ${escaparHtml(condominio.sindico.nome)}${pendente}`;
}

function montarItem(condominio) {
    // RN15: só pode inativar sem síndico, moradores ou chamados (a API informa em "pode_inativar")
    const motivoBloqueio = "Não é possível inativar: o condomínio possui síndico, moradores ou chamados.";
    const reenviar = condominio.sindico && !condominio.sindico.email_validado
        ? `<button type="button" class="btn btn-sm btn-outline-secondary" data-acao="reenviar"
                   data-id-sindico="${condominio.sindico.id}" title="Reenviar link de validação">
               <i class="bi bi-envelope"></i>
           </button>`
        : "";

    const acoes = condominio.ativo ? `
        <div class="acoes">
            ${reenviar}
            <a href="condominio.html?id=${condominio.id}" class="btn btn-sm btn-outline-secondary" title="Editar">
                <i class="bi bi-pencil"></i>
            </a>
            <span title="${condominio.pode_inativar ? "Inativar" : motivoBloqueio}">
                <button type="button" class="btn btn-sm btn-outline-danger" data-acao="inativar"
                        data-id="${condominio.id}" data-nome="${escaparHtml(condominio.nome)}"
                        ${condominio.pode_inativar ? "" : "disabled"}>
                    <i class="bi bi-trash"></i>
                </button>
            </span>
        </div>` : `<span class="badge text-bg-secondary">Inativo</span>`;

    return `
        <div class="item-lista ${condominio.ativo ? "" : "inativo"}">
            <div>
                <div class="fw-semibold">${escaparHtml(condominio.nome)}</div>
                <div class="small texto-suave">${escaparHtml(condominio.cidade)}/${escaparHtml(condominio.estado)}</div>
                <div class="small">${textoSindico(condominio)}</div>
            </div>
            ${acoes}
        </div>`;
}

async function carregarCondominios() {
    try {
        const condominios = await api(`/admin/condominios?incluir_inativos=${mostrarInativos.checked}`);
        lista.innerHTML = condominios.length
            ? condominios.map(montarItem).join("")
            : `<p class="texto-suave">Nenhum condomínio cadastrado. Comece em "Cadastrar condomínio".</p>`;
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

async function inativar(botao) {
    if (!confirm(`Inativar o condomínio "${botao.dataset.nome}"? As unidades e categorias dele também serão inativadas.`)) return;

    limparAlerta(alerta);
    try {
        await api(`/admin/condominios/${botao.dataset.id}/inativar`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Condomínio "${botao.dataset.nome}" inativado.`, "success");
        await carregarCondominios();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

async function reenviarLink(botao) {
    limparAlerta(alerta);
    definirCarregando(botao, true, "");
    try {
        // Gera um novo link e uma nova senha provisória (os anteriores deixam de valer)
        const acesso = await api(`/admin/sindicos/${botao.dataset.idSindico}/reenviar-validacao`, { metodo: "POST" });
        mostrarAcessoSindico(acessoSindico, acesso);
        acessoSindico.scrollIntoView({ behavior: "smooth" });
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botao, false);
    }
}

// Um único "ouvinte" para os botões de todos os itens da lista
lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("button[data-acao]");
    if (!botao) return;
    if (botao.dataset.acao === "inativar") inativar(botao);
    if (botao.dataset.acao === "reenviar") reenviarLink(botao);
});

mostrarInativos.addEventListener("change", carregarCondominios);

carregarCondominios();
