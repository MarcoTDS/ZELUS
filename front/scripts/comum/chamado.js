// Tela do chamado (RF18, RF09, RN03, RN06, RN10) — usada pelos dois perfis:
// Morador = "Detalhes do Chamado" (só leitura); Síndico = "Gerenciar Chamado" (altera o status).
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";
import { formatarDataHora } from "../shared/formatos.js";
import { ROTAS } from "../shared/config.js";

const usuario = await protegerPagina({ perfis: ["Morador", "Sindico"] });
montarCabecalho(usuario);

const ehSindico = usuario.perfil === "Sindico";

const $ = (id) => document.getElementById(id);
const alerta = $("alerta");
const form = $("form-status");
const novoStatus = $("novo-status");
const observacao = $("observacao");
const btnSalvar = $("btn-salvar");

// O id vem no link: chamado.html?id=32 (&novo=1 quando acabou de ser aberto)
const parametros = new URLSearchParams(window.location.search);
const idChamado = parametros.get("id");

// ==========================================
// AJUSTES POR PERFIL
// ==========================================
$("rotulo-perfil").textContent = ehSindico ? "Síndico" : "Morador";
$("titulo-pagina").textContent = ehSindico ? "Gerenciar Chamado" : "Detalhes do Chamado";

const voltar = $("link-voltar");
voltar.href = ehSindico ? ROTAS.sindico.worklist : ROTAS.inicio.Morador;
// Síndico volta para a fila (não é o dashboard): só "Voltar"
voltar.innerHTML = `<i class="bi bi-arrow-left"></i> ${ehSindico ? "Voltar" : "Voltar ao dashboard"}`;

if (ehSindico) {
    $("linha-solicitante").classList.remove("d-none");
    form.classList.remove("d-none");
} else if (parametros.get("novo")) {
    $("aviso-novo").classList.remove("d-none");
}

const CLASSES_STATUS = {
    "Aberto": "badge-aberto",
    "Em Andamento": "badge-em-andamento",
    "Resolvido": "badge-resolvido",
    "Cancelado": "badge-cancelado",
    "Vencido": "badge-vencido"
};

let chamadoAtual = null;

// ==========================================
// AJUDANTES
// ==========================================
function finalizado(status) {
    return status === "Resolvido" || status === "Cancelado";
}

// RN04: aberto com prazo estourado aparece como "Vencido"
function statusExibido(chamado) {
    return !finalizado(chamado.status) && chamado.vencido ? "Vencido" : chamado.status;
}

function formatarDuracao(ms) {
    const minutos = Math.floor(Math.abs(ms) / 60000);
    if (minutos < 60) return `${minutos} min`;
    const horas = Math.floor(minutos / 60);
    if (horas < 24) return `${horas}h`;
    const dias = Math.floor(horas / 24);
    return dias === 1 ? "1 dia" : `${dias} dias`;
}

function textoPrazo(chamado) {
    if (finalizado(chamado.status)) {
        if (chamado.concluido_no_prazo === null || chamado.concluido_no_prazo === undefined) return "Finalizado";
        return chamado.concluido_no_prazo ? "Concluído dentro do prazo" : "Concluído fora do prazo";
    }
    const restante = new Date(chamado.data_vencimento) - new Date();
    return restante > 0 ? `Expira em ${formatarDuracao(restante)}` : `Vencido há ${formatarDuracao(restante)}`;
}

// ==========================================
// PREENCHE A TELA
// ==========================================
function preencherHistorico(itens) {
    $("historico").innerHTML = itens.map((item) => `
        <p class="small mb-${item.observacao ? "0" : "2"}">
            <strong>${formatarDataHora(item.data_alteracao)}</strong> — ${escaparHtml(item.novo_status)}
        </p>
        ${item.observacao ? `<p class="small text-muted mb-2">${escaparHtml(item.observacao)}</p>` : ""}
    `).join("");
}

function preencherTela(chamado) {
    chamadoAtual = chamado;
    const status = statusExibido(chamado);

    document.title = `Chamado #${chamado.id} - Zelus`;
    $("titulo").textContent = `#${chamado.id} · ${chamado.titulo}`;

    const badge = $("status");
    badge.className = `badge ${CLASSES_STATUS[status] || "bg-secondary"}`;
    badge.textContent = status;

    $("aberto-em").textContent = `Aberto em ${formatarDataHora(chamado.data_abertura)}`;

    // RN10: o "Visto" é registrado pelo back quando o síndico abre o chamado
    const visto = $("visto");
    if (chamado.data_visto) {
        visto.textContent = `✓ Visto ${ehSindico ? "por você" : "pelo síndico"} em ${formatarDataHora(chamado.data_visto)}`;
        visto.classList.remove("d-none");
        $("nao-visto").classList.add("d-none");
    } else {
        visto.classList.add("d-none");
        $("nao-visto").classList.toggle("d-none", ehSindico);
    }

    $("solicitante").textContent = chamado.autor?.nome || "—";
    $("categoria").textContent = chamado.categoria.nome;
    $("unidade").textContent = chamado.unidade.identificacao;

    const prazo = $("prazo");
    prazo.textContent = textoPrazo(chamado);
    prazo.classList.toggle("text-danger", status === "Vencido");
    prazo.classList.toggle("fw-semibold", status === "Vencido");

    $("descricao").textContent = chamado.descricao;

    // Anexos (links)
    const foto = $("anexo-foto");
    const video = $("anexo-video");
    foto.classList.toggle("d-none", !chamado.foto_url);
    video.classList.toggle("d-none", !chamado.video_url);
    if (chamado.foto_url) foto.href = chamado.foto_url;
    if (chamado.video_url) video.href = chamado.video_url;
    $("bloco-anexo").classList.toggle("d-none", !chamado.foto_url && !chamado.video_url);

    preencherHistorico(chamado.historico || []);

    // RN06: finalizado -> esconde o formulário e mostra o aviso
    if (ehSindico) {
        const travado = finalizado(chamado.status);
        $("campos-status").classList.toggle("d-none", travado);
        $("aviso-finalizado").classList.toggle("d-none", !travado);
        if (!travado) {
            novoStatus.value = chamado.status;
            observacao.value = "";
            form.classList.remove("was-validated");
        }
    }

    $("mensagem").classList.add("d-none");
    $("conteudo").classList.remove("d-none");
}

async function carregarChamado() {
    if (!idChamado) {
        $("mensagem").textContent = "Chamado não informado.";
        return false;
    }
    try {
        preencherTela(await api(`/chamados/${encodeURIComponent(idChamado)}`));
        return true;
    } catch (erro) {
        $("mensagem").classList.add("d-none");
        mostrarAlerta(alerta, erro.message);
        return false;
    }
}

// ==========================================
// SALVAR MUDANÇA DE STATUS (síndico)
// ==========================================
form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    // Precisa escolher um status diferente do atual
    novoStatus.setCustomValidity(novoStatus.value === chamadoAtual.status ? "igual" : "");
    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        return;
    }

    // Resolvido / Cancelado travam o chamado (RN06): confirma antes
    if (finalizado(novoStatus.value) &&
        !confirm(`Marcar como "${novoStatus.value}"? Depois disso o status não poderá mais ser alterado.`)) {
        return;
    }

    const anterior = chamadoAtual.status;
    definirCarregando(btnSalvar, true, "Salvando...");
    try {
        await api(`/chamados/${encodeURIComponent(idChamado)}/status`, {
            metodo: "PATCH",
            corpo: { novo_status: novoStatus.value, observacao: observacao.value.trim() }
        });
        definirCarregando(btnSalvar, false);
        await carregarChamado();
        mostrarAlerta(alerta, `Status alterado de "${anterior}" para "${chamadoAtual.status}".`, "success");
    } catch (erro) {
        definirCarregando(btnSalvar, false);
        mostrarAlerta(alerta, erro.message);
    }
});

novoStatus.addEventListener("change", () => novoStatus.setCustomValidity(""));

await carregarChamado();