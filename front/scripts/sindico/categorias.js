// 1.12 Tela Visualizar e Cadastrar Categorias (RF08, RN01)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";
import { formatarPrazoSla } from "../shared/formatos.js";

const usuario = await protegerPagina({ perfis: ["Sindico"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const lista = document.getElementById("lista-categorias");
const mostrarInativas = document.getElementById("mostrar-inativas");
const form = document.getElementById("form-categoria");
const tituloForm = document.getElementById("titulo-form");
const campoNome = document.getElementById("nome");
const campoPrazo = document.getElementById("prazo_sla");
const campoUnidade = document.getElementById("unidade_prazo");
const btnSalvar = document.getElementById("btn-salvar");
const btnCancelar = document.getElementById("btn-cancelar");

let categorias = [];
let emEdicao = null; // categoria sendo editada (null = cadastro)

function montarItem(categoria) {
    const acoes = categoria.ativo ? `
        <div class="acoes">
            <button type="button" class="btn btn-sm btn-outline-secondary" data-acao="editar" data-id="${categoria.id}" title="Editar">
                <i class="bi bi-pencil"></i>
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" data-acao="inativar" data-id="${categoria.id}" title="Inativar">
                <i class="bi bi-trash"></i>
            </button>
        </div>` : `
        <div class="acoes">
            <span class="badge text-bg-secondary align-self-center">Inativa</span>
            <button type="button" class="btn btn-sm btn-outline-success" data-acao="reativar" data-id="${categoria.id}" title="Reativar">
                <i class="bi bi-arrow-counterclockwise"></i>
            </button>
        </div>`;

    return `
        <div class="item-lista ${categoria.ativo ? "" : "inativo"}">
            <div>
                <div class="fw-semibold">${escaparHtml(categoria.nome)}</div>
                <div class="small texto-suave">SLA: ${formatarPrazoSla(categoria.prazo_sla_horas)}</div>
            </div>
            ${acoes}
        </div>`;
}

async function carregarCategorias() {
    try {
        categorias = await api(`/categorias/?incluir_inativas=${mostrarInativas.checked}`);
        lista.innerHTML = categorias.length
            ? categorias.map(montarItem).join("")
            : `<p class="texto-suave">Nenhuma categoria cadastrada. Cadastre a primeira abaixo; os moradores só conseguem abrir chamados depois disso.</p>`;
    } catch (erro) {
        lista.innerHTML = "";
        mostrarAlerta(alerta, erro.message);
    }
}

// ==========================================
// FORMULÁRIO (cadastro e edição)
// ==========================================
function limparFormulario() {
    emEdicao = null;
    form.reset();
    form.classList.remove("was-validated");
    tituloForm.textContent = "Cadastrar categoria";
    btnSalvar.textContent = "Salvar categoria";
    btnCancelar.hidden = true;
}

function iniciarEdicao(categoria) {
    emEdicao = categoria;
    form.classList.remove("was-validated");
    campoNome.value = categoria.nome;
    campoPrazo.value = Math.round(categoria.prazo_sla_horas);
    campoUnidade.value = "horas";
    tituloForm.textContent = `Editar categoria "${categoria.nome}"`;
    btnSalvar.textContent = "Salvar alterações";
    btnCancelar.hidden = false;
    form.scrollIntoView({ behavior: "smooth", block: "center" });
    campoNome.focus();
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);
    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    const dados = {
        nome: campoNome.value.trim(),
        prazo_sla: Number(campoPrazo.value),
        unidade_prazo: campoUnidade.value
    };

    definirCarregando(btnSalvar, true, "Salvando...");
    try {
        if (emEdicao) {
            // RN01: o novo prazo vale só para os chamados abertos daqui em diante
            await api(`/categorias/${emEdicao.id}`, { metodo: "PUT", corpo: dados });
            mostrarAlerta(alerta, `Categoria "${dados.nome}" atualizada. O novo prazo vale para os próximos chamados.`, "success");
        } else {
            await api("/categorias/", { metodo: "POST", corpo: dados });
            mostrarAlerta(alerta, `Categoria "${dados.nome}" cadastrada.`, "success");
        }
        definirCarregando(btnSalvar, false);
        limparFormulario();
        await carregarCategorias();
    } catch (erro) {
        definirCarregando(btnSalvar, false);
        mostrarAlerta(alerta, erro.message);
    }
});

btnCancelar.addEventListener("click", limparFormulario);

// ==========================================
// AÇÕES DA LISTA
// ==========================================
async function alterarSituacao(categoria, ativar) {
    if (!ativar && !confirm(`Inativar a categoria "${categoria.nome}"? Ela deixa de aparecer na abertura de chamados.`)) return;

    limparAlerta(alerta);
    try {
        if (ativar) {
            await api(`/categorias/${categoria.id}`, { metodo: "PUT", corpo: { ativo: true } });
        } else {
            await api(`/categorias/${categoria.id}/inativar`, { metodo: "PATCH" });
        }
        if (emEdicao?.id === categoria.id) limparFormulario();
        mostrarAlerta(alerta, `Categoria "${categoria.nome}" ${ativar ? "reativada" : "inativada"}.`, "success");
        await carregarCategorias();
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-acao]");
    if (!botao) return;
    const categoria = categorias.find((c) => c.id === Number(botao.dataset.id));

    if (botao.dataset.acao === "editar") iniciarEdicao(categoria);
    if (botao.dataset.acao === "inativar") alterarSituacao(categoria, false);
    if (botao.dataset.acao === "reativar") alterarSituacao(categoria, true);
});

mostrarInativas.addEventListener("change", carregarCategorias);

await carregarCategorias();
