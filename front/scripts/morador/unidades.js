// Minhas Unidades (RF06): unidades do morador, pedido de vínculo com outra unidade e saída de uma unidade
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Morador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-vinculos");
const form = document.getElementById("form-solicitar");
const selectUnidade = document.getElementById("unidade");
const botaoSolicitar = document.getElementById("btn-solicitar");

let vinculos = [];

const CLASSES_STATUS = {
    Aprovado: "text-bg-success",
    Pendente: "text-bg-warning",
    Rejeitado: "text-bg-danger"
};

const TEXTOS_STATUS = {
    Aprovado: "Aprovada",
    Pendente: "Aguardando síndico",
    Rejeitado: "Rejeitada"
};

// A última unidade aprovada não pode ser deixada pelo morador (a saída do condomínio é com o síndico)
function podeEncerrar(vinculo) {
    if (vinculo.status_aprovacao !== "Aprovado") return true;
    return vinculos.filter((v) => v.status_aprovacao === "Aprovado").length > 1;
}

function montarItem(vinculo) {
    const textoAcao = vinculo.status_aprovacao === "Aprovado" ? "Sair da unidade"
        : vinculo.status_aprovacao === "Pendente" ? "Cancelar solicitação" : "Remover da lista";
    const acao = podeEncerrar(vinculo) ? `
        <button type="button" class="btn btn-sm btn-outline-danger" data-id="${vinculo.id}" title="${textoAcao}">
            <i class="bi bi-x-circle"></i> <span class="d-none d-sm-inline">${textoAcao}</span>
        </button>` : `
        <span class="small texto-suave" title="Para deixar o condomínio, procure o síndico">Unidade principal</span>`;

    return `
        <div class="item-lista">
            <div>
                <div class="fw-semibold">${escaparHtml(vinculo.unidade.identificacao)}</div>
                <span class="badge ${CLASSES_STATUS[vinculo.status_aprovacao] || "bg-secondary"}">
                    ${escaparHtml(TEXTOS_STATUS[vinculo.status_aprovacao] || vinculo.status_aprovacao)}
                </span>
            </div>
            <div class="acoes">${acao}</div>
        </div>`;
}

async function carregarVinculos() {
    vinculos = await api("/vinculos/meus");
    lista.innerHTML = vinculos.length
        ? vinculos.map(montarItem).join("")
        : `<p class="texto-suave">Nenhuma unidade encontrada.</p>`;
}

// Unidades do condomínio do morador que ainda não estão pendentes ou aprovadas para ele
async function carregarUnidadesDisponiveis() {
    const unidades = await api(`/publico/condominios/${usuario.id_condominio}/unidades`, { autenticado: false });
    const ocupadas = new Set(vinculos
        .filter((v) => v.status_aprovacao !== "Rejeitado")
        .map((v) => v.id_unidade));
    const disponiveis = unidades.filter((u) => !ocupadas.has(u.id));

    selectUnidade.innerHTML = "";
    selectUnidade.add(new Option(disponiveis.length ? "Selecione a unidade" : "Nenhuma outra unidade disponível", ""));
    for (const unidade of disponiveis) {
        selectUnidade.add(new Option(unidade.identificacao, unidade.id));
    }
    selectUnidade.disabled = disponiveis.length === 0;
    botaoSolicitar.disabled = disponiveis.length === 0;
}

async function recarregar() {
    try {
        await carregarVinculos();
        await carregarUnidadesDisponiveis();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

lista.addEventListener("click", async (evento) => {
    const botao = evento.target.closest("button[data-id]");
    if (!botao) return;

    const vinculo = vinculos.find((v) => v.id === Number(botao.dataset.id));
    const pergunta = vinculo.status_aprovacao === "Aprovado"
        ? `Sair da unidade ${vinculo.unidade.identificacao}?\n\nVocê não poderá mais abrir chamados para ela. Os chamados já abertos continuam no histórico.`
        : `Cancelar a solicitação da unidade ${vinculo.unidade.identificacao}?`;
    if (vinculo.status_aprovacao !== "Rejeitado" && !confirm(pergunta)) return;

    limparAlerta(alerta);
    definirCarregando(botao, true, "");
    try {
        await api(`/vinculos/${vinculo.id}/encerrar`, { metodo: "PATCH" });
        await recarregar();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
});

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botaoSolicitar, true, "Enviando...");
    try {
        await api("/vinculos/solicitar", { metodo: "POST", corpo: { id_unidade: Number(selectUnidade.value) } });
        definirCarregando(botaoSolicitar, false);
        form.classList.remove("was-validated");
        await recarregar();
        mostrarAlerta(alerta, "Solicitação enviada. A unidade fica pendente até a aprovação do síndico.", "success");
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botaoSolicitar, false);
    }
});

await recarregar();
