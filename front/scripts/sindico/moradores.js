// 1.14 Tela Gerenciamento de Moradores (RF21, RN08)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
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
        morador.unidades.push(vinculo.unidade.identificacao);
        porId.set(morador.id, morador);
    }
    return [...porId.values()];
}

function montarItem(morador) {
    const unidades = escaparHtml(morador.unidades.join(" · "));
    const acoes = morador.ativo ? `
        <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="editar" data-id="${morador.id}" title="Editar">
            <i class="bi bi-pencil"></i>
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
                <div class="small texto-suave">${unidades}${morador.ativo ? "" : " · Inativo"}</div>
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
            <div class="small texto-suave mt-1">${escaparHtml(morador.unidades.join(" · "))}</div>
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

async function carregarMoradores() {
    try {
        moradores = agruparPorMorador(await api("/moradores/"));
        renderizar();
    } catch (erro) {
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

lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-acao]");
    if (!botao) return;
    const morador = moradores.find((m) => m.id === Number(botao.dataset.id));

    if (botao.dataset.acao === "editar") { emEdicao = morador.id; limparAlerta(alerta); renderizar(); }
    if (botao.dataset.acao === "cancelar") { emEdicao = null; renderizar(); }
    if (botao.dataset.acao === "inativar") alterarSituacao(morador, false);
    if (botao.dataset.acao === "reativar") alterarSituacao(morador, true);
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
