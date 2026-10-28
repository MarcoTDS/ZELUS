// 1.14 Tela Gerenciamento de Moradores (RF21, RN08)
// "Inativar" só bloqueia o acesso do morador; "Desvincular" (botão da casa) encerra o vínculo com uma unidade:
// com mais de uma unidade a janela pede para escolher qual; com uma só, a janela pede a confirmação.
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { atualizarPeriodicamente } from "../shared/atualizacao.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-moradores");

let moradores = [];   // um item por morador, com todas as unidades aprovadas dele
let emEdicao = null;  // id do morador com o formulário de edição aberto

// A API devolve um item por vínculo (morador + unidade); aqui juntamos as unidades de cada morador
function agruparPorMorador(vinculos) {
    const porId = new Map();
    for (const vinculo of vinculos) {
        const morador = porId.get(vinculo.usuario.id) || { ...vinculo.usuario, unidades: [] };
        morador.unidades.push({ idVinculo: vinculo.id, identificacao: vinculo.unidade.identificacao });
        porId.set(morador.id, morador);
    }
    return [...porId.values()];
}

function nomesDasUnidades(morador) {
    return escaparHtml(morador.unidades.map((u) => u.identificacao).join(" · "));
}

// Unidades do morador (a remoção é feita pelo botão "Desvincular" das ações)
function montarUnidades(morador) {
    return `<span>${nomesDasUnidades(morador)}</span> `;
}

function montarItem(morador) {
    const acoes = morador.ativo ? `
        <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="editar" data-id="${morador.id}" title="Editar">
            <i class="bi bi-pencil"></i>
        </button>
        <button type="button" class="btn btn-sm btn-outline-danger" data-acao="desvincular" data-id="${morador.id}"
                title="Desvincular de uma unidade" aria-label="Desvincular ${escaparHtml(morador.nome)} de uma unidade">
            <i class="bi bi-house-dash"></i>
        </button>
        <button type="button" class="btn btn-sm btn-outline-danger" data-acao="inativar" data-id="${morador.id}" title="Inativar">
            <i class="bi bi-person-x"></i>
        </button>` : `
        <button type="button" class="btn btn-sm btn-outline-secondary" disabled title="Reative o morador para editar">
            <i class="bi bi-pencil"></i>
        </button>
        <button type="button" class="btn btn-sm btn-outline-success" data-acao="reativar" data-id="${morador.id}" title="Reativar">
            <i class="bi bi-person-check"></i>
        </button>`;

    return `
        <div class="item-lista ${morador.ativo ? "" : "inativo"}">
            <div>
                <div class="fw-semibold">${escaparHtml(morador.nome)}</div>
                <div class="small texto-suave">${montarUnidades(morador)}${morador.ativo ? "" : "<span>Inativo</span>"}</div>
            </div>
            <div class="acoes">${acoes}</div>
        </div>`;
}

function montarFormEdicao(morador) {
    return `
        <form class="item-lista d-block" data-form-id="${morador.id}" novalidate>
            <div class="row g-2">
                <div class="col-sm">
                    <label class="form-label small mb-1" for="editar-nome">Nome</label>
                    <input type="text" class="form-control form-control-sm" id="editar-nome" name="nome"
                           value="${escaparHtml(morador.nome)}" required minlength="3" maxlength="150">
                    <div class="invalid-feedback">Informe o nome (mínimo 3 caracteres).</div>
                </div>
                <div class="col-sm">
                    <label class="form-label small mb-1" for="editar-email">E-mail</label>
                    <input type="email" class="form-control form-control-sm" id="editar-email" name="email"
                           value="${escaparHtml(morador.email)}" required>
                    <div class="invalid-feedback">Informe um e-mail válido.</div>
                </div>
            </div>
            <div class="small texto-suave mt-1">${nomesDasUnidades(morador)}</div>
            <div class="d-flex gap-2 justify-content-end mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="cancelar">Cancelar</button>
                <button type="submit" class="btn btn-sm btn-zelus">Salvar</button>
            </div>
        </form>`;
}

function renderizar() {
    if (!moradores.length) {
        lista.innerHTML = `<p class="texto-suave">Nenhum morador aprovado ainda. Os novos cadastros aparecem em
            <a href="${ROTAS.sindico.cadastrosPendentes}">Cadastros pendentes</a>.</p>`;
        return;
    }
    lista.innerHTML = moradores.map((m) => (m.id === emEdicao ? montarFormEdicao(m) : montarItem(m))).join("");
    if (emEdicao) document.getElementById("editar-nome").focus();
}

async function carregarMoradores({ silencioso = false } = {}) {
    try {
        moradores = agruparPorMorador(await api("/moradores/"));
        renderizar();
    } catch (erro) {
        if (silencioso) throw erro;
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

async function alterarSituacao(morador, ativar) {
    const pergunta = ativar
        ? `Reativar ${morador.nome}? O acesso ao sistema volta a ser liberado.`
        : `Inativar ${morador.nome}? O acesso ao sistema será bloqueado, mas os chamados abertos continuam no histórico.`;
    if (!confirm(pergunta)) return;

    limparAlerta(alerta);
    try {
        await api(`/moradores/${morador.id}/${ativar ? "reativar" : "inativar"}`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Morador ${morador.nome} ${ativar ? "reativado" : "inativado"}.`, "success");
        await carregarMoradores();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

// RF21: encerra o vínculo do morador com a unidade. Sem outra unidade, a API também bloqueia o acesso.
async function executarRemocao(morador, idVinculo) {
    const unidade = morador.unidades.find((u) => u.idVinculo === idVinculo);

    limparAlerta(alerta);
    try {
        const resultado = await api(`/moradores/vinculos/${idVinculo}/remover`, { metodo: "PATCH" });
        const complemento = resultado.usuario_inativado ? " Sem outra unidade, o acesso ao sistema foi bloqueado até ele solicitar uma nova unidade pelo cadastro, com o mesmo e-mail." : "";
        mostrarAlerta(alerta, `Vínculo de ${morador.nome} com a unidade ${unidade.identificacao} removido.${complemento}`, "success");
        await carregarMoradores();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

// ==========================================
// JANELA PARA ESCOLHER A UNIDADE A DESVINCULAR
// ==========================================
// Montada uma vez e reaproveitada (fica fora de #lista-moradores para não sumir quando a lista atualiza)
document.body.insertAdjacentHTML("beforeend", `
    <div class="modal fade" id="modal-desvincular" tabindex="-1" aria-labelledby="titulo-desvincular" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header border-0 pb-0">
                    <h2 class="modal-title h5 fw-semibold" id="titulo-desvincular"></h2>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                </div>
                <div class="modal-body">
                    <p class="small texto-suave mb-3" id="texto-desvincular"></p>
                    <div class="list-group" id="opcoes-desvincular"></div>
                </div>
                <div class="modal-footer border-0 pt-0">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="button" class="btn btn-danger" id="btn-confirmar-desvincular" disabled>Desvincular</button>
                </div>
            </div>
        </div>
    </div>`);

const elementoModal = document.getElementById("modal-desvincular");
const modalDesvincular = new bootstrap.Modal(elementoModal);
const opcoesDesvincular = document.getElementById("opcoes-desvincular");
const btnConfirmarDesvincular = document.getElementById("btn-confirmar-desvincular");
let moradorDoModal = null;

function abrirModalDesvincular(morador) {
    moradorDoModal = morador.id;
    const titulo = document.getElementById("titulo-desvincular");
    const texto = document.getElementById("texto-desvincular");

    if (morador.unidades.length === 1) {
        // Única unidade: só confirma (o acesso ao sistema também é bloqueado)
        const unidade = morador.unidades[0];
        titulo.textContent = "Desvincular morador?";
        texto.textContent = `Esta é a única unidade de ${morador.nome}. Ao desvincular, ele(a) sai da lista de moradores e o acesso ao sistema será bloqueado.`;
        opcoesDesvincular.innerHTML = `
            <div class="list-group-item d-flex align-items-center gap-3">
                <i class="bi bi-house-door text-danger"></i>
                <span class="fw-semibold">${escaparHtml(unidade.identificacao)}</span>
            </div>`;
        btnConfirmarDesvincular.disabled = false;
    } else {
        titulo.textContent = "Desvincular de qual unidade?";
        texto.textContent = `${morador.nome} continua nas outras unidades. Escolha a unidade da qual ele(a) será removido(a).`;
        opcoesDesvincular.innerHTML = morador.unidades.map((unidade) => `
            <label class="list-group-item d-flex align-items-center gap-3" style="cursor: pointer;">
                <input class="form-check-input mt-0" type="radio" name="unidade-desvincular" value="${unidade.idVinculo}">
                <span class="fw-semibold">${escaparHtml(unidade.identificacao)}</span>
            </label>`).join("");
        btnConfirmarDesvincular.disabled = true;
    }
    modalDesvincular.show();
}

opcoesDesvincular.addEventListener("change", () => { btnConfirmarDesvincular.disabled = false; });

btnConfirmarDesvincular.addEventListener("click", async () => {
    const morador = moradores.find((m) => m.id === moradorDoModal);
    if (!morador) return;

    // Uma unidade só: é a própria; senão, a que foi marcada
    const escolhida = opcoesDesvincular.querySelector("input:checked");
    const idVinculo = morador.unidades.length === 1 ? morador.unidades[0].idVinculo : Number(escolhida?.value);
    if (!idVinculo) return;

    modalDesvincular.hide();
    await executarRemocao(morador, idVinculo);
});

elementoModal.addEventListener("hidden.bs.modal", () => { moradorDoModal = null; });

// Abre a janela: escolher a unidade (mais de uma) ou confirmar (uma só)
function desvincular(morador) {
    abrirModalDesvincular(morador);
}

lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-acao]");
    if (!botao) return;
    const morador = moradores.find((m) => m.id === Number(botao.dataset.id));

    if (botao.dataset.acao === "editar") { emEdicao = morador.id; limparAlerta(alerta); renderizar(); }
    if (botao.dataset.acao === "cancelar") { emEdicao = null; renderizar(); }
    if (botao.dataset.acao === "inativar") alterarSituacao(morador, false);
    if (botao.dataset.acao === "reativar") alterarSituacao(morador, true);
    if (botao.dataset.acao === "desvincular") desvincular(morador);
});

lista.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const form = evento.target;
    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    const botao = form.querySelector("[type=submit]");
    limparAlerta(alerta);
    definirCarregando(botao, true, "Salvando...");
    try {
        await api(`/moradores/${form.dataset.formId}`, {
            metodo: "PUT",
            corpo: { nome: form.nome.value.trim(), email: form.email.value.trim() }
        });
        emEdicao = null;
        mostrarAlerta(alerta, "Dados do morador atualizados.", "success");
        await carregarMoradores();
    } catch (erro) {
        definirCarregando(botao, false);
        mostrarAlerta(alerta, erro.message);
    }
});

await carregarMoradores();

// Moradores aprovados em "Cadastros pendentes" aparecem sem recarregar a página.
// Pausa enquanto um morador está em edição ou uma ação ainda está em andamento.
atualizarPeriodicamente(async () => {
    if (emEdicao || moradorDoModal || lista.querySelector(".spinner-border")) return;
    await carregarMoradores({ silencioso: true });
});