// Dashboard do Morador (RF14): atalho para abrir chamado e lista dos chamados dele
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, escaparHtml } from "../shared/ui.js";
import { ROTAS } from "../shared/config.js";

const usuario = await protegerPagina({ perfis: ["Morador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-chamados");
const campoBusca = document.getElementById("busca");

// Nome de um campo que pode vir como texto ou como objeto (ex.: { nome } ou { identificacao })
function nomeDe(valor) {
    if (!valor) return "";
    if (typeof valor === "string") return valor;
    return valor.identificacao || valor.nome || "";
}

const info = [nomeDe(usuario.unidade), nomeDe(usuario.condominio)].filter(Boolean).join(" · ");
document.getElementById("info-morador").textContent = info;

const CLASSES_STATUS = {
    "Aberto": "badge-aberto",
    "Em Andamento": "badge-em-andamento",
    "Resolvido": "badge-resolvido",
    "Cancelado": "badge-cancelado"
};

let chamados = [];

function finalizado(status) {
    return status === "Resolvido" || status === "Cancelado";
}

function formatarData(texto) {
    return new Date(texto).toLocaleDateString("pt-BR");
}

// RN04: a cor da lateral vem da urgência calculada pelo back (None se finalizado)
function montarItem(chamado) {
    const vencido = !finalizado(chamado.status) && chamado.vencido;
    const status = vencido ? "Vencido" : chamado.status;
    const classeBadge = vencido ? "badge-vencido" : (CLASSES_STATUS[chamado.status] || "bg-secondary");
    const urgencia = chamado.urgencia ? ` urgencia-${chamado.urgencia.toLowerCase()}` : "";

    return `
        <a href="${ROTAS.comum.chamado}?id=${encodeURIComponent(chamado.id)}" class="item-chamado${urgencia}">
            <div class="d-flex justify-content-between align-items-center gap-2">
                <span class="fw-semibold">#${chamado.id} · ${escaparHtml(chamado.titulo)}</span>
                <span class="badge ${classeBadge}">${escaparHtml(status)}</span>
            </div>
            <p class="small detalhe mb-0">
                ${escaparHtml(nomeDe(chamado.categoria))} · ${escaparHtml(nomeDe(chamado.unidade))} · Aberto em ${formatarData(chamado.data_abertura)}
            </p>
        </a>`;
}

function desenharLista() {
    const termo = campoBusca.value.replace(/\D/g, "");
    const visiveis = chamados.filter((c) => !termo || String(c.id).includes(termo));

    if (visiveis.length === 0) {
        lista.innerHTML = `<p class="texto-suave">${chamados.length === 0
            ? 'Você ainda não abriu nenhum chamado. Use "Abrir Chamado" para registrar um problema.'
            : "Nenhum chamado encontrado com esse número."}</p>`;
        return;
    }
    lista.innerHTML = visiveis.map(montarItem).join("");
}

document.getElementById("form-busca").addEventListener("submit", (evento) => {
    evento.preventDefault();
    desenharLista();
});

// Limpou o campo -> volta a lista toda
campoBusca.addEventListener("input", () => {
    if (!campoBusca.value) desenharLista();
});

async function carregarChamados() {
    try {
        chamados = await api("/chamados/meus");
        const emAberto = chamados.filter((c) => !finalizado(c.status)).length;
        document.getElementById("resumo-lista").textContent = chamados.length ? `${emAberto} em aberto` : "";
        desenharLista();
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

await carregarChamados();