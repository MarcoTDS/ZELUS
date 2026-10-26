// 1.9 Tela Dashboard do Perfil Síndico (RF03, RN18)
import { api, sessao } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { atualizarPeriodicamente } from "../shared/atualizacao.js";
import { mostrarAlerta, limparAlerta, mostrarAvisoPendente, definirCarregando } from "../shared/ui.js";

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
    liberarSaida(resumo.abertos);
}

// RN18: "Sair do condomínio" só fica disponível sem chamados Aberto ou Em Andamento
const botaoSair = document.getElementById("btn-sair-condominio");
const motivoSair = document.getElementById("motivo-sair");

function liberarSaida(chamadosEmAberto) {
    botaoSair.disabled = chamadosEmAberto > 0;
    motivoSair.hidden = chamadosEmAberto === 0;
    motivoSair.textContent = `Há ${chamadosEmAberto} chamado(s) Aberto ou Em Andamento. Resolva antes de sair.`;
}

botaoSair.addEventListener("click", async () => {
    if (!confirm("Sair do condomínio?\n\nSeu acesso como síndico será encerrado e o condomínio ficará sem síndico até o administrador cadastrar outro.")) return;

    limparAlerta(alerta);
    definirCarregando(botaoSair, true, "Saindo...");
    try {
        await api("/auth/me/sair-do-condominio", { metodo: "PATCH" });
        sessao.limpar();
        window.location.replace(`${ROTAS.login}?motivo=saiu`);
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botaoSair, false);
    }
});

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

// Novos chamados e cadastros aparecem sem recarregar a página
atualizarPeriodicamente(() => Promise.all([carregarResumo(), carregarPendentes()]));
