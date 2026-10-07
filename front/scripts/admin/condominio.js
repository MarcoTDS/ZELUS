// 1.20 Tela de Cadastro de Condomínio (RF12) e edição (RN15, RF20)
// Sem parâmetro: cadastra o condomínio com as unidades em lote (POST /admin/condominios).
// Com ?id=N: edita o endereço (PUT) e adiciona/inativa unidades direto na API.
import { api } from "../shared/api.js";
import { ROTAS } from "../shared/config.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml, avisarNaProximaTela } from "../shared/ui.js";
import { buscarEnderecoPorCep } from "../shared/cep.js";

const usuario = await protegerPagina({ perfis: ["Administrador"] });
montarCabecalho(usuario);

const UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB",
             "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"];
const CAMPOS_ENDERECO = ["nome", "cep", "rua", "numero", "bairro", "cidade", "estado"];

// Campos da unidade conforme o tipo: [campo1, campo2 (obrigatório)]
const CAMPOS_POR_TIPO = {
    "Apartamento": [{ nome: "bloco", rotulo: "Bloco (ex: A)" }, { nome: "apartamento", rotulo: "Apto (ex: 21)" }],
    "Casa": [{ nome: "rua", rotulo: "Rua interna (opcional)" }, { nome: "numero_casa", rotulo: "Nº da casa" }],
    "Area Comum": [{ nome: "descricao", rotulo: "Descrição (ex: Garagem)" }, null]
};

const form = document.getElementById("form-condominio");
const alerta = document.getElementById("alerta");
const alertaUnidade = document.getElementById("alerta-unidade");
const listaUnidades = document.getElementById("lista-unidades");
const botaoSalvar = document.getElementById("btn-salvar");
const botaoAdicionar = document.getElementById("btn-adicionar");
const tipoUnidade = document.getElementById("tipo_unidade");
const campo1 = document.getElementById("campo1");
const campo2 = document.getElementById("campo2");
const statusCep = document.getElementById("status-cep");

const idCondominio = new URLSearchParams(window.location.search).get("id");
const modoEdicao = Boolean(idCondominio);

// No cadastro: unidades ainda não gravadas. Na edição: unidades vindas da API.
let unidades = [];

// ==========================================
// FORMULÁRIO DE ENDEREÇO
// ==========================================
for (const uf of UFS) form.estado.add(new Option(uf, uf));

// Máscara simples de CEP: 00000-000. Com os 8 dígitos, busca o endereço no ViaCEP.
form.cep.addEventListener("input", () => {
    const digitos = form.cep.value.replace(/\D/g, "").slice(0, 8);
    form.cep.value = digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos;

    if (digitos.length === 8) {
        preencherEnderecoPeloCep(digitos);
    } else {
        statusCep.textContent = "";
    }
});

// Guarda o último CEP consultado, para ignorar respostas antigas se o usuário digitar outro CEP rápido
let cepConsultado = null;

async function preencherEnderecoPeloCep(cep) {
    cepConsultado = cep;
    statusCep.className = "form-text";
    statusCep.textContent = "Buscando endereço...";

    try {
        const endereco = await buscarEnderecoPorCep(cep);
        if (cep !== cepConsultado) return;

        if (!endereco) {
            statusCep.className = "form-text text-danger";
            statusCep.textContent = "CEP não encontrado. Confira o número ou preencha o endereço manualmente.";
            return;
        }

        form.rua.value = endereco.rua;
        form.bairro.value = endereco.bairro;
        form.cidade.value = endereco.cidade;
        form.estado.value = endereco.estado;
        statusCep.textContent = "";

        // CEP geral (cidade pequena) não traz rua: o cursor vai para a rua; senão, para o número
        (endereco.rua ? form.numero : form.rua).focus();
    } catch (erro) {
        if (cep !== cepConsultado) return;
        statusCep.className = "form-text text-warning-emphasis";
        statusCep.textContent = erro.message;
    }
}

function dadosEndereco() {
    const dados = {};
    for (const campo of CAMPOS_ENDERECO) dados[campo] = form[campo].value.trim();
    return dados;
}

// ==========================================
// UNIDADES
// ==========================================
// Mesmo texto que a API monta em "identificacao" (ex: "Bloco A, Apto 21")
function identificar(unidade) {
    if (unidade.tipo_unidade === "Apartamento") {
        return [unidade.bloco && `Bloco ${unidade.bloco}`, `Apto ${unidade.apartamento}`].filter(Boolean).join(", ");
    }
    if (unidade.tipo_unidade === "Casa") {
        return [unidade.rua, `Casa ${unidade.numero_casa}`].filter(Boolean).join(", ");
    }
    return unidade.descricao;
}

function atualizarCamposUnidade() {
    const [primeiro, segundo] = CAMPOS_POR_TIPO[tipoUnidade.value];
    campo1.placeholder = primeiro.rotulo;
    campo1.setAttribute("aria-label", primeiro.rotulo);
    document.getElementById("coluna-campo2").hidden = !segundo;
    if (segundo) {
        campo2.placeholder = segundo.rotulo;
        campo2.setAttribute("aria-label", segundo.rotulo);
    }
}

function lerNovaUnidade() {
    const tipo = tipoUnidade.value;
    const [primeiro, segundo] = CAMPOS_POR_TIPO[tipo];
    const unidade = { tipo_unidade: tipo, [primeiro.nome]: campo1.value.trim() || null };
    if (segundo) unidade[segundo.nome] = campo2.value.trim() || null;

    // Campo obrigatório de cada tipo (o mesmo que a API valida)
    const obrigatorio = segundo ? segundo : primeiro;
    if (!unidade[obrigatorio.nome]) {
        throw new Error(`Preencha o campo "${obrigatorio.rotulo}".`);
    }

    const identificacao = identificar(unidade).toLowerCase();
    if (unidades.some((u) => (u.identificacao || identificar(u)).toLowerCase() === identificacao)) {
        throw new Error(`A unidade "${identificar(unidade)}" já está na lista.`);
    }
    return unidade;
}

function renderizarUnidades() {
    if (!unidades.length) {
        listaUnidades.innerHTML = `<p class="small texto-suave mb-0">Nenhuma unidade adicionada.</p>`;
        return;
    }
    listaUnidades.innerHTML = unidades.map((unidade, indice) => {
        // RN17: unidade com morador responsável não pode ser inativada
        const bloqueada = Boolean(unidade.responsavel);
        const detalhe = bloqueada ? `<span class="small texto-suave"> · Responsável: ${escaparHtml(unidade.responsavel)}</span>` : "";
        return `
            <div class="item-lista py-2">
                <span class="small">${escaparHtml(unidade.identificacao || identificar(unidade))}${detalhe}</span>
                <button type="button" class="btn btn-link btn-sm text-danger p-0" data-indice="${indice}"
                        ${bloqueada ? "disabled title='A unidade possui morador responsável'" : ""}>Remover</button>
            </div>`;
    }).join("");
}

async function adicionarUnidade() {
    limparAlerta(alertaUnidade);
    let unidade;
    try {
        unidade = lerNovaUnidade();
    } catch (erro) {
        mostrarAlerta(alertaUnidade, erro.message, "warning");
        return;
    }

    if (modoEdicao) {
        definirCarregando(botaoAdicionar, true, "");
        try {
            const criada = await api(`/admin/condominios/${idCondominio}/unidades`, { metodo: "POST", corpo: unidade });
            unidades.push(criada);
        } catch (erro) {
            mostrarAlerta(alertaUnidade, erro.message);
            return;
        } finally {
            definirCarregando(botaoAdicionar, false);
        }
    } else {
        unidades.push(unidade);
    }

    campo1.value = "";
    campo2.value = "";
    (CAMPOS_POR_TIPO[tipoUnidade.value][1] ? campo2 : campo1).focus();
    renderizarUnidades();
}

async function removerUnidade(indice) {
    limparAlerta(alertaUnidade);
    const unidade = unidades[indice];

    if (modoEdicao) {
        if (!confirm(`Inativar a unidade "${unidade.identificacao}"?`)) return;
        try {
            await api(`/admin/condominios/${idCondominio}/unidades/${unidade.id}/inativar`, { metodo: "PATCH" });
        } catch (erro) {
            mostrarAlerta(alertaUnidade, erro.message);
            return;
        }
    }
    unidades.splice(indice, 1);
    renderizarUnidades();
}

tipoUnidade.addEventListener("change", atualizarCamposUnidade);
botaoAdicionar.addEventListener("click", adicionarUnidade);

// Enter nos campos da unidade adiciona a unidade
for (const campo of [campo1, campo2]) {
    campo.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            evento.preventDefault();
            adicionarUnidade();
        }
    });
}

listaUnidades.addEventListener("click", (evento) => {
    const botao = evento.target.closest("button[data-indice]");
    if (botao) removerUnidade(Number(botao.dataset.indice));
});

// ==========================================
// CARREGAR (EDIÇÃO) E SALVAR
// ==========================================
async function carregarCondominio() {
    document.getElementById("titulo").textContent = "Editar condomínio";
    document.title = "Editar condomínio | Zelus";
    botaoSalvar.textContent = "Salvar alterações";

    try {
        // A API não tem GET de um condomínio só: busca na listagem do administrador
        const condominios = await api("/admin/condominios");
        const condominio = condominios.find((c) => c.id === Number(idCondominio));
        if (!condominio) throw new Error("Condomínio não encontrado ou inativo.");

        for (const campo of CAMPOS_ENDERECO) form[campo].value = condominio[campo] ?? "";
        unidades = await api(`/admin/condominios/${idCondominio}/unidades`);
        renderizarUnidades();
    } catch (erro) {
        form.hidden = true;
        document.getElementById("secao-unidades").hidden = true;
        botaoSalvar.hidden = true;
        mostrarAlerta(alerta, erro.message);
    }
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    if (!modoEdicao && unidades.length === 0) {
        mostrarAlerta(alertaUnidade, "Adicione pelo menos uma unidade ao condomínio.", "warning");
        return;
    }

    definirCarregando(botaoSalvar, true, "Salvando...");
    try {
        if (modoEdicao) {
            await api(`/admin/condominios/${idCondominio}`, { metodo: "PUT", corpo: dadosEndereco() });
            avisarNaProximaTela("Condomínio atualizado.");
            window.location.replace(ROTAS.inicio.Administrador);
        } else {
            const criado = await api("/admin/condominios", {
                metodo: "POST",
                corpo: { ...dadosEndereco(), unidades }
            });
            // Próximo passo natural: cadastrar o síndico do condomínio novo (RF13)
            avisarNaProximaTela(`Condomínio "${criado.nome}" cadastrado com ${unidades.length} unidade(s). Agora cadastre o síndico.`);
            window.location.replace(`${ROTAS.admin.cadastroSindico}?condominio=${criado.id}`);
        }
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        alerta.scrollIntoView({ behavior: "smooth" });
        definirCarregando(botaoSalvar, false);
    }
});

atualizarCamposUnidade();
if (modoEdicao) {
    await carregarCondominio();
} else {
    renderizarUnidades();
}
