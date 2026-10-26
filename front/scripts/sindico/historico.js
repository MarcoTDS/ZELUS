// Tela Histórico de Chamados (RF22)
// Todos os chamados do condomínio, inclusive resolvidos e cancelados.
// Carrega a lista uma vez e aplica busca e filtros na própria tela.
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { mostrarAlerta, limparAlerta, escaparHtml } from "../shared/ui.js";
import { formatarTicket, descreverPrazo, seloStatus, formatarDataHora } from "../shared/formatos.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-chamados");
const resumo = document.getElementById("resumo");
const formBusca = document.getElementById("form-busca");
const campoTicket = document.getElementById("ticket");
const filtroStatus = document.getElementById("filtro-status");
const filtroDe = document.getElementById("filtro-de");
const filtroAte = document.getElementById("filtro-ate");
const painelFiltro = document.getElementById("painel-filtro");
const btnFiltro = document.getElementById("btn-filtro");
const indicadorFiltro = document.getElementById("indicador-filtro");

// Todos os chamados como vieram da API
let chamados = [];

function finalizado(chamado) {
    return chamado.status === "Resolvido" || chamado.status === "Cancelado";
}

// Chamado ainda em andamento e com o prazo estourado (RN04)
function estaVencido(chamado) {
    return !finalizado(chamado) && (chamado.vencido || chamado.urgencia === "Vencido");
}

// Dia local no formato do campo date (AAAA-MM-DD)
function diaLocal(texto) {
    const data = new Date(texto);
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${data.getFullYear()}-${mes}-${dia}`;
}

function montarItem(chamado) {
    const urgencia = finalizado(chamado) ? "" : (chamado.urgencia || "").toLowerCase();
    const classeUrgencia = urgencia ? `urgencia-${urgencia}` : "";

    // Finalizado: não faz sentido falar em "expira em"; mostra só quando foi aberto
    const situacao = finalizado(chamado)
        ? chamado.status
        : descreverPrazo(chamado.data_vencimento);

    return `
        <a href="${ROTAS.comum.chamado}?id=${chamado.id}" class="item-chamado ${classeUrgencia}">
            <div class="d-flex justify-content-between align-items-start gap-2">
                <span class="fw-semibold">${formatarTicket(chamado.id)} · ${escaparHtml(chamado.titulo)}</span>
                ${seloStatus(chamado)}
            </div>
            <div class="small detalhe">
                ${escaparHtml(chamado.categoria.nome)} · ${escaparHtml(chamado.unidade.identificacao)}
                · Aberto em ${formatarDataHora(chamado.data_abertura)} · ${situacao}
            </div>
        </a>`;
}

function filtrosAtivos() {
    return Boolean(filtroStatus.value || filtroDe.value || filtroAte.value);
}

function aplicarFiltros() {
    limparAlerta(alerta);
    const ticket = campoTicket.value.replace(/\D/g, ""); // aceita "#0030" ou "30"

    const visiveis = chamados.filter((chamado) => {
        const dia = diaLocal(chamado.data_abertura);
        if (ticket && !String(chamado.id).includes(ticket)) return false;
        if (filtroStatus.value === "Vencido") {
            if (!estaVencido(chamado)) return false;
        } else if (filtroStatus.value && chamado.status !== filtroStatus.value) {
            return false;
        }
        if (filtroDe.value && dia < filtroDe.value) return false;
        if (filtroAte.value && dia > filtroAte.value) return false;
        return true;
    });

    indicadorFiltro.classList.toggle("d-none", !filtrosAtivos());

    if (visiveis.length === 0) {
        const mensagem = chamados.length === 0
            ? "Nenhum chamado registrado ainda."
            : "Nenhum chamado encontrado com essa busca/filtro.";
        lista.innerHTML = `<p class="texto-suave">${mensagem}</p>`;
        return;
    }
    lista.innerHTML = visiveis.map(montarItem).join("");
}

function plural(quantidade, singular, pluralTexto) {
    return `${quantidade} ${quantidade === 1 ? singular : pluralTexto}`;
}

function atualizarResumo() {
    if (!chamados.length) {
        resumo.textContent = "";
        return;
    }
    const abertos = chamados.filter((chamado) => !finalizado(chamado)).length;
    const resolvidos = chamados.filter((chamado) => chamado.status === "Resolvido").length;
    const cancelados = chamados.filter((chamado) => chamado.status === "Cancelado").length;
    resumo.textContent = [
        plural(chamados.length, "chamado", "chamados"),
        `${abertos} em aberto`,
        plural(resolvidos, "resolvido", "resolvidos"),
        plural(cancelados, "cancelado", "cancelados")
    ].join(" · ");
}

async function carregarHistorico() {
    limparAlerta(alerta);
    try {
        chamados = await api("/chamados/historico");
        atualizarResumo();
        aplicarFiltros();
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

formBusca.addEventListener("submit", (evento) => {
    evento.preventDefault();
    aplicarFiltros();
});
// O "x" do campo de busca limpa o filtro do ticket
campoTicket.addEventListener("search", () => { if (!campoTicket.value) aplicarFiltros(); });

btnFiltro.addEventListener("click", () => {
    const abrir = painelFiltro.classList.contains("d-none");
    painelFiltro.classList.toggle("d-none", !abrir);
    btnFiltro.setAttribute("aria-expanded", String(abrir));
});

[filtroStatus, filtroDe, filtroAte].forEach((campo) => {
    campo.addEventListener("change", aplicarFiltros);
});

document.getElementById("btn-limpar").addEventListener("click", () => {
    filtroStatus.value = "";
    filtroDe.value = "";
    filtroAte.value = "";
    aplicarFiltros();
});

await carregarHistorico();