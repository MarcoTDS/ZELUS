// 1.10 Tela Fila de Chamados - Worklist (RF10, RN04, RN14)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { mostrarAlerta, limparAlerta, escaparHtml } from "../shared/ui.js";
import { formatarTicket, descreverPrazo, seloStatus } from "../shared/formatos.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-chamados");
const formBusca = document.getElementById("form-busca");
const campoTicket = document.getElementById("ticket");
const filtroStatus = document.getElementById("filtro-status");

function montarItem(chamado) {
    // RN04: a cor da borda indica a urgência do SLA (Vencido, Alta, Media, Baixa)
    const urgencia = (chamado.urgencia || "").toLowerCase();
    return `
        <a href="${ROTAS.comum.chamado}?id=${chamado.id}" class="item-chamado urgencia-${urgencia}">
            <div class="d-flex justify-content-between align-items-start gap-2">
                <span class="fw-semibold">${formatarTicket(chamado.id)} · ${escaparHtml(chamado.titulo)}</span>
                ${seloStatus(chamado)}
            </div>
            <div class="small detalhe">
                ${escaparHtml(chamado.categoria.nome)} · ${escaparHtml(chamado.unidade.identificacao)} · ${descreverPrazo(chamado.data_vencimento)}
            </div>
        </a>`;
}

async function carregarChamados() {
    limparAlerta(alerta);
    const ticket = campoTicket.value.replace(/\D/g, ""); // aceita "#0030" ou "30"
    const filtros = new URLSearchParams();
    if (ticket) filtros.set("ticket", ticket);
    if (filtroStatus.value) filtros.set("status", filtroStatus.value);

    try {
        const chamados = await api(`/chamados/worklist?${filtros}`);
        if (chamados.length) {
            lista.innerHTML = chamados.map(montarItem).join("");
        } else if (ticket || filtroStatus.value) {
            lista.innerHTML = `<p class="texto-suave">Nenhum chamado em aberto encontrado com esse filtro.
                Chamados resolvidos ou cancelados ficam no <a href="${ROTAS.sindico.historico}">Histórico</a>.</p>`;
        } else {
            lista.innerHTML = `<p class="texto-suave">Nenhum chamado em aberto no momento.</p>`;
        }
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

formBusca.addEventListener("submit", (evento) => {
    evento.preventDefault();
    carregarChamados();
});
filtroStatus.addEventListener("change", carregarChamados);
// O "x" do campo de busca limpa o filtro do ticket
campoTicket.addEventListener("search", () => { if (!campoTicket.value) carregarChamados(); });

await carregarChamados();
