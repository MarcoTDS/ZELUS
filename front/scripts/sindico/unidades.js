// 1.15 Tela Gerenciamento de Unidades (RF20, RN17)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

// Campos da unidade conforme o tipo: [campo1, campo2]. O obrigatório é o último (o mesmo que a API valida).
const CAMPOS_POR_TIPO = {
    "Apartamento": [{ nome: "bloco", rotulo: "Bloco (ex: A)" }, { nome: "apartamento", rotulo: "Apto (ex: 21)" }],
    "Casa": [{ nome: "rua", rotulo: "Rua interna (opcional)" }, { nome: "numero_casa", rotulo: "Nº da casa" }],
    "Area Comum": [{ nome: "descricao", rotulo: "Descrição (ex: Garagem)" }, null]
};

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-unidades");
const form = document.getElementById("form-unidade");
const tipoUnidade = document.getElementById("tipo_unidade");
const campo1 = document.getElementById("campo1");
const campo2 = document.getElementById("campo2");
const btnAdicionar = document.getElementById("btn-adicionar");

let unidades = [];
let emEdicao = null; // id da unidade com o formulário de edição aberto

function campoObrigatorio(tipo) {
    const [primeiro, segundo] = CAMPOS_POR_TIPO[tipo];
    return segundo || primeiro;
}

// Lê os campos de um tipo e devolve o objeto para a API (ou um erro se faltar o obrigatório)
function lerUnidade(tipo, valor1, valor2) {
    const [primeiro, segundo] = CAMPOS_POR_TIPO[tipo];
    const unidade = { [primeiro.nome]: valor1.trim() || null };
    if (segundo) unidade[segundo.nome] = valor2.trim() || null;

    const obrigatorio = campoObrigatorio(tipo);
    if (!unidade[obrigatorio.nome]) {
        throw new Error(`Preencha o campo "${obrigatorio.rotulo.replace(/ \(.*\)/, "")}".`);
    }
    return unidade;
}

// ==========================================
// LISTA
// ==========================================
function montarItem(unidade) {
    // RN17: unidade com morador responsável não pode ser inativada (lixeira desabilitada)
    const bloqueada = Boolean(unidade.responsavel);
    const detalhe = unidade.tipo_unidade === "Area Comum"
        ? "Área comum"
        : (bloqueada ? `Responsável: ${escaparHtml(unidade.responsavel)}` : "Sem morador responsável");

    return `
        <div class="item-lista">
            <div>
                <div class="fw-semibold">${escaparHtml(unidade.identificacao)}</div>
                <div class="small texto-suave">${detalhe}</div>
            </div>
            <div class="acoes">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="editar" data-id="${unidade.id}" title="Editar">
                    <i class="bi bi-pencil"></i>
                </button>
                <span title="${bloqueada ? "A unidade possui morador responsável e não pode ser removida" : "Remover (inativar)"}">
                    <button type="button" class="btn btn-sm btn-outline-danger" data-acao="inativar" data-id="${unidade.id}"
                            ${bloqueada ? "disabled" : ""}>
                        <i class="bi bi-trash"></i>
                    </button>
                </span>
            </div>
        </div>`;
}

function montarFormEdicao(unidade) {
    const [primeiro, segundo] = CAMPOS_POR_TIPO[unidade.tipo_unidade];
    const campo = (definicao, numero) => `
        <div class="col">
            <label class="form-label small mb-1" for="editar-campo${numero}">${definicao.rotulo}</label>
            <input type="text" class="form-control form-control-sm" id="editar-campo${numero}" name="campo${numero}"
                   value="${escaparHtml(unidade[definicao.nome])}" maxlength="${numero === 1 ? 150 : 50}">
        </div>`;

    return `
        <form class="item-lista d-block" data-form-id="${unidade.id}" novalidate>
            <div class="small texto-suave mb-1">${unidade.tipo_unidade === "Area Comum" ? "Área comum" : unidade.tipo_unidade}</div>
            <div class="row g-2">
                ${campo(primeiro, 1)}
                ${segundo ? campo(segundo, 2) : ""}
            </div>
            <div class="d-flex gap-2 justify-content-end mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="cancelar">Cancelar</button>
                <button type="submit" class="btn btn-sm btn-zelus">Salvar</button>
            </div>
        </form>`;
}

function renderizar() {
    if (!unidades.length) {
        lista.innerHTML = `<p class="texto-suave">Nenhuma unidade cadastrada. Adicione a primeira abaixo.</p>`;
        return;
    }
    lista.innerHTML = unidades.map((u) => (u.id === emEdicao ? montarFormEdicao(u) : montarItem(u))).join("");
    if (emEdicao) document.getElementById("editar-campo1").focus();
}

async function carregarUnidades() {
    try {
        unidades = await api("/unidades/");
        renderizar();
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

async function inativar(unidade) {
    if (!confirm(`Remover a unidade "${unidade.identificacao}"? Ela deixa de aparecer no cadastro de moradores e na abertura de chamados.`)) return;

    limparAlerta(alerta);
    try {
        await api(`/unidades/${unidade.id}/inativar`, { metodo: "PATCH" });
        mostrarAlerta(alerta, `Unidade "${unidade.identificacao}" removida.`, "success");
        await carregarUnidades();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-acao]");
    if (!botao) return;
    const unidade = unidades.find((u) => u.id === Number(botao.dataset.id));

    if (botao.dataset.acao === "editar") { emEdicao = unidade.id; limparAlerta(alerta); renderizar(); }
    if (botao.dataset.acao === "cancelar") { emEdicao = null; renderizar(); }
    if (botao.dataset.acao === "inativar") inativar(unidade);
});

lista.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const formEdicao = evento.target;
    const unidade = unidades.find((u) => u.id === Number(formEdicao.dataset.formId));
    limparAlerta(alerta);

    let dados;
    try {
        dados = lerUnidade(unidade.tipo_unidade, formEdicao.campo1.value, formEdicao.campo2?.value || "");
    } catch (erro) {
        mostrarAlerta(alerta, erro.message, "warning");
        return;
    }

    const botao = formEdicao.querySelector("[type=submit]");
    definirCarregando(botao, true, "Salvando...");
    try {
        const atualizada = await api(`/unidades/${unidade.id}`, { metodo: "PUT", corpo: dados });
        emEdicao = null;
        mostrarAlerta(alerta, `Unidade "${atualizada.identificacao}" atualizada.`, "success");
        await carregarUnidades();
    } catch (erro) {
        definirCarregando(botao, false);
        mostrarAlerta(alerta, erro.message);
    }
});

// ==========================================
// ADICIONAR
// ==========================================
function atualizarCamposNovaUnidade() {
    const [primeiro, segundo] = CAMPOS_POR_TIPO[tipoUnidade.value];
    campo1.placeholder = primeiro.rotulo;
    campo1.setAttribute("aria-label", primeiro.rotulo);
    document.getElementById("coluna-campo2").hidden = !segundo;
    if (segundo) {
        campo2.placeholder = segundo.rotulo;
        campo2.setAttribute("aria-label", segundo.rotulo);
    }
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    let dados;
    try {
        dados = { tipo_unidade: tipoUnidade.value, ...lerUnidade(tipoUnidade.value, campo1.value, campo2.value) };
    } catch (erro) {
        mostrarAlerta(alerta, erro.message, "warning");
        return;
    }

    definirCarregando(btnAdicionar, true, "Adicionando...");
    try {
        const criada = await api("/unidades/", { metodo: "POST", corpo: dados });
        mostrarAlerta(alerta, `Unidade "${criada.identificacao}" adicionada.`, "success");
        campo1.value = "";
        campo2.value = "";
        (CAMPOS_POR_TIPO[tipoUnidade.value][1] ? campo2 : campo1).focus();
        await carregarUnidades();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(btnAdicionar, false);
    }
});

tipoUnidade.addEventListener("change", atualizarCamposNovaUnidade);
atualizarCamposNovaUnidade();

await carregarUnidades();
