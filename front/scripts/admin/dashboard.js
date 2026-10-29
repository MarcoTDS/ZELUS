// 1.19 Tela Dashboard do Perfil Administrador (RF04, RN12, RN15)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, mostrarAvisoPendente, escaparHtml, definirCarregando, confirmar } from "../shared/ui.js";
import { mostrarAcessoSindico } from "./acesso-sindico.js";
import { atualizarPeriodicamente } from "../shared/atualizacao.js";

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

// Dica exibida na lixeira desabilitada, com o que falta fazer para liberar a inativação (RN15)
const COMO_LIBERAR = {
    "o condomínio possui um síndico vinculado": "Desvincule o síndico primeiro.",
    "o condomínio possui moradores vinculados": "O síndico precisa remover os moradores das unidades (tela Moradores).",
    "o condomínio possui chamados em aberto": "Os chamados precisam ser resolvidos ou cancelados."
};

function montarItem(condominio) {
    // RN15: só pode inativar sem síndico, moradores ou chamados em aberto (a API informa em "pode_inativar")
    const motivo = condominio.motivo_bloqueio || "o condomínio possui vínculos ativos";
    const motivoBloqueio = `Não é possível inativar: ${motivo}. ${COMO_LIBERAR[motivo] || ""}`.trim();
    const desvincular = condominio.sindico
        ? `<button type="button" class="btn btn-sm btn-outline-secondary" data-acao="desvincular"
                   data-id="${condominio.id}" data-nome="${escaparHtml(condominio.nome)}"
                   data-sindico="${escaparHtml(condominio.sindico.nome)}" title="Desvincular síndico">
               <i class="bi bi-person-dash"></i>
           </button>`
        : "";
    const reenviar = condominio.sindico && !condominio.sindico.email_validado
        ? `<button type="button" class="btn btn-sm btn-outline-secondary" data-acao="reenviar"
                   data-id-sindico="${condominio.sindico.id}" title="Reenviar link de validação">
               <i class="bi bi-envelope"></i>
           </button>`
        : "";

    const acoes = condominio.ativo ? `
        <div class="acoes">
            ${reenviar}
            ${desvincular}
            <a href="cadastro-condominio.html?id=${condominio.id}" class="btn btn-sm btn-outline-secondary" title="Editar">
                <i class="bi bi-pencil"></i>
            </a>
            <span title="${condominio.pode_inativar ? "Inativar" : motivoBloqueio}">
                <button type="button" class="btn btn-sm btn-outline-danger" data-acao="inativar"
                        data-id="${condominio.id}" data-nome="${escaparHtml(condominio.nome)}"
                        ${condominio.pode_inativar ? "" : "disabled"}>
                    <i class="bi bi-trash"></i>
                </button>
            </span>
        </div>` : `
        <div class="acoes">
            <span class="badge text-bg-secondary">Inativo</span>
            <button type="button" class="btn btn-sm btn-outline-success" data-acao="reativar"
                    data-id="${condominio.id}" data-nome="${escaparHtml(condominio.nome)}" title="Reativar">
                <i class="bi bi-arrow-counterclockwise"></i>
            </button>
        </div>`;

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

async function carregarCondominios({ silencioso = false } = {}) {
    try {
        const condominios = await api(`/admin/condominios?incluir_inativos=${mostrarInativos.checked}`);
        lista.innerHTML = condominios.length
            ? condominios.map(montarItem).join("")
            : `<p class="texto-suave">Nenhum condomínio cadastrado. Comece em "Cadastrar condomínio".</p>`;
    } catch (erro) {
        if (silencioso) throw erro;
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

async function inativar(botao) {
    if (!(await confirmar({
        titulo: "Inativar condomínio?",
        mensagem: `O condomínio "${botao.dataset.nome}" será inativado. As unidades e categorias dele também serão inativadas.`,
        textoConfirmar: "Inativar"
    }))) return;

    limparAlerta(alerta);
    try {
        await api(`/admin/condominios/${botao.dataset.id}/inativar`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Condomínio "${botao.dataset.nome}" inativado.`, "success");
        await carregarCondominios();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

// Desfaz a inativação: o condomínio, as unidades e as categorias voltam a ficar ativos (sem síndico)
async function reativar(botao) {
    if (!(await confirmar({
        titulo: "Reativar condomínio?",
        mensagem: `As unidades e categorias de "${botao.dataset.nome}" voltam a ficar ativas. O condomínio volta sem síndico: cadastre um novo depois.`,
        textoConfirmar: "Reativar",
        perigo: false
    }))) return;

    limparAlerta(alerta);
    definirCarregando(botao, true, "");
    try {
        await api(`/admin/condominios/${botao.dataset.id}/reativar`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Condomínio "${botao.dataset.nome}" reativado.`, "success");
        await carregarCondominios();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
}

// RN07: tira o síndico do condomínio (troca de síndico ou encerramento). O acesso do síndico é bloqueado.
async function desvincularSindico(botao) {
    const { id, nome, sindico } = botao.dataset;
    if (!(await confirmar({
        titulo: "Desvincular síndico?",
        mensagem: `${sindico} será desvinculado do condomínio "${nome}". O acesso de ${sindico} ao sistema será bloqueado e o condomínio ficará sem síndico até você cadastrar outro.\n\nSe a ideia é inativar o condomínio, peça antes ao síndico para remover os moradores das unidades e encerrar os chamados em aberto.`,
        textoConfirmar: "Desvincular"
    }))) return;

    limparAlerta(alerta);
    try {
        await api(`/admin/condominios/${id}/desvincular-sindico`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Síndico desvinculado do condomínio "${nome}" (${sindico}).`, "success");
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
    if (botao.dataset.acao === "reativar") reativar(botao);
    if (botao.dataset.acao === "reenviar") reenviarLink(botao);
    if (botao.dataset.acao === "desvincular") desvincularSindico(botao);
});

mostrarInativos.addEventListener("change", () => carregarCondominios());

carregarCondominios();

// Validação do e-mail do síndico, saída do síndico e o que bloqueia a inativação (RN15)
// aparecem sem recarregar a página. Pausa enquanto uma ação ainda está em andamento.
atualizarPeriodicamente(async () => {
    if (lista.querySelector(".spinner-border")) return;
    await carregarCondominios({ silencioso: true });
});