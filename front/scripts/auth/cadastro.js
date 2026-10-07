// 1.3 Tela de Cadastro (RF05, RF06, RN11)
import { api } from "../shared/api.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";

const form = document.getElementById("form-cadastro");
const botao = document.getElementById("btn-enviar");
const alerta = document.getElementById("alerta");
const selectCondominio = form.condominio;
const selectUnidade = form.unidade;

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

async function carregarUnidades(idCondominio) {
    selectUnidade.disabled = true;

    if (!idCondominio) {
        preencherSelect(selectUnidade, "Escolha o condomínio antes", [], null);
        return;
    }

    preencherSelect(selectUnidade, "Carregando...", [], null);
    try {
        // Somente casas e apartamentos (as áreas comuns não aparecem no cadastro)
        const unidades = await api(`/publico/condominios/${idCondominio}/unidades`, { autenticado: false });
        if (unidades.length === 0) {
            preencherSelect(selectUnidade, "Nenhuma unidade disponível", [], null);
            return;
        }
        preencherSelect(selectUnidade, "Selecione a unidade", unidades, (u) => u.identificacao);
        selectUnidade.disabled = false;
    } catch (erro) {
        preencherSelect(selectUnidade, "Não foi possível carregar", [], null);
        mostrarAlerta(alerta, erro.message);
    }
}

// Exibe a confirmação no lugar do formulário
function mostrarSucesso(mensagem) {
    const cartao = form.closest(".cartao-auth");
    cartao.innerHTML = `
        <header class="mb-3">
            <h1 class="h4 mb-1">Solicitação enviada</h1>
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
    if (!form.checkValidity()) return;

    definirCarregando(botao, true, "Enviando...");
    try {
        const resposta = await api("/auth/cadastro", {
            metodo: "POST",
            autenticado: false,
            corpo: {
                nome: form.nome.value.trim(),
                email: form.email.value.trim(),
                senha: form.senha.value,
                id_unidade: Number(selectUnidade.value)
            }
        });
        mostrarSucesso(resposta.mensagem);
    } catch (erro) {
        // 409: e-mail já cadastrado (RN11) | 404: unidade não encontrada ou inativada
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
});

carregarCondominios();
