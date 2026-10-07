// 1.9 Tela Dashboard do Perfil Síndico (RF03)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, mostrarAvisoPendente } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
mostrarAvisoPendente(alerta);

// Resumo dos chamados em aberto do condomínio do síndico (RN14)
async function carregarResumo() {
    const resumo = await api("/chamados/resumo");
    document.getElementById("resumo-abertos").textContent = resumo.abertos;
    document.getElementById("resumo-urgentes").textContent = resumo.urgentes;
    document.getElementById("resumo-vencidos").textContent = resumo.vencidos;
}

// Quantidade de cadastros aguardando aprovação, exibida no atalho "Aprovar cadastros" (RF11)
async function carregarPendentes() {
    const pendentes = await api("/vinculos/pendentes");
    const selo = document.getElementById("qtd-pendentes");
    selo.textContent = pendentes.length;
    selo.title = `${pendentes.length} cadastro(s) aguardando aprovação`;
    selo.hidden = pendentes.length === 0;
}

const resultados = await Promise.allSettled([carregarResumo(), carregarPendentes()]);
const falha = resultados.find((resultado) => resultado.status === "rejected");
if (falha) {
    mostrarAlerta(alerta, falha.reason.message);
}
