// Tela Mural do Condomínio (RF17, RN05) — só para o morador.
// Todos os chamados do condomínio, só para consulta. Carrega a lista uma vez
// e aplica busca e filtro na própria tela.
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { mostrarAlerta, limparAlerta, escaparHtml } from "../shared/ui.js";
import { formatarTicket, descreverPrazo, seloStatus, formatarDataHora } from "../shared/formatos.js";

const usuario = await protegerPagina({ perfis: ["Morador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-chamados");
const resumo = document.getElementById("resumo");
const formBusca = document.getElementById("form-busca");
const campoTicket = document.getElementById("ticket");
const filtroStatus = document.getElementById("filtro-status");

// Todos os chamados como vieram da API
let chamados = [];

function finalizado(chamado) {
    return chamado.status === "Resolvido" || chamado.status === "Cancelado";
}

function montarItem(chamado) {
    const urgencia = finalizado(chamado) ? "" : (chamado.urgencia || "").toLowerCase();
    const classeUrgencia = urgencia ? `urgencia-${urgencia}` : "";

    // Se a API informar quem abriu / se é do morador logado, mostramos; senão, só a data
    const solicitante = chamado.meu ? "você" : (chamado.solicitante || chamado.autor?.nome || "");
    const abertoPor = solicitante ? ` por ${escaparHtml(solicitante)}` : "";
    const selo = chamado.meu ? `<span class="badge badge-voce">Você</span>` : "";

    const situacao = finalizado(chamado) ? chamado.status : descreverPrazo(chamado.data_vencimento);

    return `
        <a href="${ROTAS.comum.chamado}?id=${chamado.id}" class="item-chamado ${classeUrgencia}">
            <div class="d-flex justify-content-between align-items-start gap-2">
                <span class="fw-semibold">${formatarTicket(chamado.id)} · ${escaparHtml(chamado.titulo)}</span>
                <span class="d-flex gap-1 flex-shrink-0">${selo}${seloStatus(chamado)}</span>
            </div>
            <div class="small detalhe">
                ${escaparHtml(chamado.categoria.nome)} · ${escaparHtml(chamado.unidade.identificacao)}
                · Aberto em ${formatarDataHora(chamado.data_abertura)}${abertoPor} · ${situacao}
            </div>
        </a>`;
}

function aplicarFiltros() {
    limparAlerta(alerta);
    const ticket = campoTicket.value.replace(/\D/g, ""); // aceita "#0030" ou "30"
    const situacao = filtroStatus.value;

    const visiveis = chamados.filter((chamado) => {
        if (ticket && !String(chamado.id).includes(ticket)) return false;
        if (situacao === "abertos" && finalizado(chamado)) return false;
        if (situacao === "finalizados" && !finalizado(chamado)) return false;
        return true;
    });

    const abertos = chamados.filter((chamado) => !finalizado(chamado)).length;
    resumo.textContent = chamados.length
        ? `${abertos} ${abertos === 1 ? "chamado em aberto" : "chamados em aberto"}`
        : "";

    if (visiveis.length === 0) {
        let mensagem;
        if (chamados.length === 0) mensagem = "Nenhum chamado registrado no condomínio ainda.";
        else if (ticket) mensagem = "Nenhum chamado encontrado com esse número.";
        else if (situacao === "abertos") mensagem = "Nenhum chamado em aberto no condomínio. Tudo em dia!";
        else mensagem = "Nenhum chamado nessa situação.";
        lista.innerHTML = `<p class="texto-suave">${mensagem}</p>`;
        return;
    }
    lista.innerHTML = visiveis.map(montarItem).join("");
}

async function carregarMural() {
    limparAlerta(alerta);
    try {
        chamados = await api("/chamados/mural");
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
filtroStatus.addEventListener("change", aplicarFiltros);

await carregarMural();