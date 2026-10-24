// 1.3 Tela de Cadastro (RF05, RF06, RN11): uma ou mais unidades do mesmo condomínio
import { api } from "../shared/api.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";

const form = document.getElementById("form-cadastro");
const botao = document.getElementById("btn-enviar");
const alerta = document.getElementById("alerta");
const selectCondominio = form.condominio;
const listaUnidades = document.getElementById("lista-unidades");
const erroUnidades = document.getElementById("erro-unidades");

// Preenche um <select> com uma opção inicial e a lista recebida da API
function preencherSelect(select, textoInicial, itens, textoDoItem) {
    select.innerHTML = "";
    select.add(new Option(textoInicial, ""));
    for (const item of itens) {
        select.add(new Option(textoDoItem(item), item.id));
    }
}

async function carregarCondominios() {
    try {
        const condominios = await api("/publico/condominios", { autenticado: false });
        preencherSelect(selectCondominio, "Selecione o condomínio", condominios,
            (c) => `${c.nome} (${c.cidade}/${c.estado})`);
    } catch (erro) {
        preencherSelect(selectCondominio, "Não foi possível carregar", [], null);
        mostrarAlerta(alerta, erro.message);
    }
}

function mostrarTextoUnidades(texto) {
    listaUnidades.innerHTML = `<p class="small texto-suave mb-0">${escaparHtml(texto)}</p>`;
}

// RF06: o morador pode marcar mais de uma unidade do mesmo condomínio
async function carregarUnidades(idCondominio) {
    erroUnidades.hidden = true;

    if (!idCondominio) {
        mostrarTextoUnidades("Escolha o condomínio antes.");
        return;
    }

    mostrarTextoUnidades("Carregando...");
    try {
        // Somente casas e apartamentos (as áreas comuns não aparecem no cadastro)
        const unidades = await api(`/publico/condominios/${idCondominio}/unidades`, { autenticado: false });
        if (unidades.length === 0) {
            mostrarTextoUnidades("Nenhuma unidade disponível.");
            return;
        }
        listaUnidades.innerHTML = unidades.map((u) => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="unidades" value="${u.id}" id="unidade-${u.id}">
                <label class="form-check-label small" for="unidade-${u.id}">${escaparHtml(u.identificacao)}</label>
            </div>`).join("");
    } catch (erro) {
        mostrarTextoUnidades("Não foi possível carregar.");
        mostrarAlerta(alerta, erro.message);
    }
}

function unidadesMarcadas() {
    return [...listaUnidades.querySelectorAll("input[name=unidades]:checked")].map((caixa) => Number(caixa.value));
}

listaUnidades.addEventListener("change", () => {
    erroUnidades.hidden = unidadesMarcadas().length > 0;
});

// Exibe a confirmação no lugar do formulário
function mostrarSucesso(mensagem) {
    // Cartão do layout novo (.card-body); mantém .cartao-auth como alternativa
    const cartao = form.closest(".card-body") || form.closest(".cartao-auth");
    cartao.innerHTML = `
        <header class="mb-3">
            <h1 class="h4 mb-1">Solicitação Enviada</h1>
        </header>
        <div class="alert alert-success py-2" role="status"></div>
        <a href="login.html" class="btn btn-zelus w-100">Voltar para o login</a>
    `;
    cartao.querySelector(".alert").textContent = mensagem;
}

selectCondominio.addEventListener("change", () => carregarUnidades(selectCondominio.value));

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    const idsUnidades = unidadesMarcadas();
    erroUnidades.hidden = idsUnidades.length > 0;
    if (!form.checkValidity() || idsUnidades.length === 0) return;

    definirCarregando(botao, true, "Enviando...");
    try {
        const resposta = await api("/auth/cadastro", {
            metodo: "POST",
            autenticado: false,
            corpo: {
                nome: form.nome.value.trim(),
                email: form.email.value.trim(),
                senha: form.senha.value,
                ids_unidades: idsUnidades
            }
        });
        mostrarSucesso(resposta.mensagem || "Cadastro enviado! Aguarde a aprovação do síndico.");
    } catch (erro) {
        // 409: e-mail já cadastrado (RN11) | 404: unidade não encontrada ou inativada | 400: unidades de condomínios diferentes
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
});

carregarCondominios();