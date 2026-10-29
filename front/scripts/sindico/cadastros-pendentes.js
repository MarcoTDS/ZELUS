// 1.13 Tela Aprovar/Rejeitar Cadastro (RF11, RN11)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml, confirmar } from "../shared/ui.js";
import { formatarDataHora } from "../shared/formatos.js";
import { atualizarPeriodicamente } from "../shared/atualizacao.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-pendentes");

let pendentes = [];
let avaliando = false; // evita redesenhar a lista no meio de uma aprovação/rejeição

const LISTA_VAZIA = `<p class="texto-suave">Nenhum cadastro aguardando aprovação.</p>`;

function montarCartao(vinculo) {
    // RN11: a unidade já tem responsável -> aviso e "Aprovar mesmo assim"
    const comResponsavel = Boolean(vinculo.responsavel_atual);
    const aviso = comResponsavel ? `
        <div class="alert alert-danger py-2 px-3 small mt-2 mb-0">
            <i class="bi bi-exclamation-triangle"></i>
            Unidade já possui responsável: ${escaparHtml(vinculo.responsavel_atual)}
        </div>` : "";

    return `
        <div class="cartao-pendente ${comResponsavel ? "com-aviso" : ""}" data-id="${vinculo.id}">
            <div class="fw-semibold">${escaparHtml(vinculo.usuario.nome)}</div>
            <div class="small texto-suave">${escaparHtml(vinculo.usuario.email)}</div>
            <div class="small">${escaparHtml(vinculo.unidade.identificacao)}</div>
            <div class="small texto-suave">Solicitado em ${formatarDataHora(vinculo.data_solicitacao)}</div>
            ${aviso}
            <div class="row g-2 mt-1">
                <div class="col">
                    <button type="button" class="btn btn-outline-secondary bg-white w-100" data-acao="aprovar">
                        ${comResponsavel ? "Aprovar mesmo assim" : "Aprovar"}
                    </button>
                </div>
                <div class="col">
                    <button type="button" class="btn btn-outline-danger bg-white text-danger w-100" data-acao="rejeitar">Rejeitar</button>
                </div>
            </div>
        </div>`;
}

function renderizar() {
    lista.innerHTML = pendentes.length ? pendentes.map(montarCartao).join("") : LISTA_VAZIA;
}

async function carregarPendentes({ silencioso = false } = {}) {
    try {
        pendentes = await api("/vinculos/pendentes");
        renderizar();
    } catch (erro) {
        if (silencioso) throw erro;
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

async function avaliar(botao, aprovado) {
    const cartao = botao.closest("[data-id]");
    const vinculo = pendentes.find((v) => v.id === Number(cartao.dataset.id));
    const nome = vinculo.usuario.nome;

    if (!aprovado && !(await confirmar({
        titulo: "Rejeitar cadastro?",
        mensagem: `O cadastro de ${nome} na unidade ${vinculo.unidade.identificacao} será rejeitado.`,
        textoConfirmar: "Rejeitar"
    }))) return;

    limparAlerta(alerta);
    avaliando = true;
    definirCarregando(botao, true, aprovado ? "Aprovando..." : "Rejeitando...");
    cartao.querySelectorAll("button").forEach((b) => { b.disabled = true; });
    try {
        await api(`/vinculos/${vinculo.id}/avaliar`, { metodo: "PATCH", corpo: { aprovado } });
        mostrarAlerta(alerta, aprovado
            ? `Cadastro de ${nome} aprovado. O morador já pode acessar o sistema.`
            : `Cadastro de ${nome} rejeitado.`, "success");
        // Recarrega: aprovar alguém muda o aviso de "unidade já possui responsável" dos outros pedidos
        await carregarPendentes();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        await carregarPendentes();
    } finally {
        avaliando = false;
    }
}

lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-acao]");
    if (botao) avaliar(botao, botao.dataset.acao === "aprovar");
});

await carregarPendentes();

// Novos pedidos de cadastro aparecem sem recarregar a página
atualizarPeriodicamente(async () => {
    if (!avaliando) await carregarPendentes({ silencioso: true });
});