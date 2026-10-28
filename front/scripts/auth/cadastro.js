// 1.3 Tela de Cadastro (RF05, RF06, RN11): uma ou mais unidades do mesmo condomínio
// O e-mail é consultado no banco ao ser digitado: conta nova exibe nome, senha, condomínio e unidade;
// morador sem unidade (conta já existente) exibe só a senha atual, condomínio e unidade.
import { api } from "../shared/api.js";
import { mostrarAlerta, limparAlerta, definirCarregando, escaparHtml } from "../shared/ui.js";

const form = document.getElementById("form-cadastro");
const botao = document.getElementById("btn-enviar");
const alerta = document.getElementById("alerta");
const selectCondominio = form.condominio;
const listaUnidades = document.getElementById("lista-unidades");
const erroUnidades = document.getElementById("erro-unidades");
const campoEmail = form.email;
const infoEmail = document.getElementById("info-email");
const grupoNome = document.getElementById("grupo-nome");
const grupoSenha = document.getElementById("grupo-senha");
const grupoUnidades = document.getElementById("grupo-unidades");
const rotuloSenha = document.getElementById("rotulo-senha");
const ajudaSenha = document.getElementById("ajuda-senha");

const SENHA_MIN = 6;
const ESPERA_DIGITACAO = 500; // ms sem digitar antes de consultar o e-mail

let situacao = null;       // "novo" | "sem_unidade" | "existente" | null (e-mail ainda não verificado)
let emailVerificado = "";  // Último e-mail consultado (evita repetir a consulta)
let consultaAtual = null;  // Consulta em andamento (o envio do formulário espera por ela)
let temporizador = null;

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

// ==========================================
// VERIFICAÇÃO DO E-MAIL (consulta no banco, sem envio de e-mail)
// ==========================================
// Mostra ou esconde um grupo de campos; campos escondidos ficam desabilitados e não entram na validação
function exibirGrupo(grupo, visivel) {
    grupo.hidden = !visivel;
    grupo.querySelectorAll("input, select").forEach((campo) => { campo.disabled = !visivel; });
}

function mostrarInfoEmail(texto, tipo = "") {
    infoEmail.className = `form-text${tipo ? ` text-${tipo}` : ""}`;
    infoEmail.innerHTML = texto;
}

function aplicarSituacao(nova) {
    situacao = nova;
    const podeSolicitar = nova === "novo" || nova === "sem_unidade";

    exibirGrupo(grupoNome, nova === "novo");
    exibirGrupo(grupoSenha, podeSolicitar);
    exibirGrupo(grupoUnidades, podeSolicitar);

    form.senha.value = "";
    if (nova === "novo") {
        rotuloSenha.textContent = "Senha";
        ajudaSenha.textContent = `Mínimo de ${SENHA_MIN} caracteres.`;
        form.senha.minLength = SENHA_MIN;
        form.senha.autocomplete = "new-password";
        mostrarInfoEmail("");
    } else if (nova === "sem_unidade") {
        rotuloSenha.textContent = "Senha atual";
        ajudaSenha.innerHTML = 'Informe a senha da sua conta para confirmar que é você. <a href="esqueci-senha.html" class="link-zelus">Esqueceu a senha?</a>';
        form.senha.minLength = 0;
        form.senha.autocomplete = "current-password";
        mostrarInfoEmail("Você já tem uma conta no Zelus. Escolha o condomínio e a(s) unidade(s) para solicitar um novo vínculo.", "success");
    } else if (nova === "existente") {
        mostrarInfoEmail('Este e-mail já possui uma conta. <a href="login.html" class="link-zelus">Entre pelo login</a>.', "danger");
    } else {
        mostrarInfoEmail("Digite seu e-mail para continuar.");
    }
}

async function verificarEmail() {
    const email = campoEmail.value.trim();
    if (!email || !campoEmail.checkValidity()) {
        emailVerificado = "";
        if (situacao !== null) aplicarSituacao(null);
        return;
    }
    if (email === emailVerificado) return;

    mostrarInfoEmail("Verificando e-mail...");
    try {
        const resposta = await api("/auth/cadastro/verificar-email", {
            metodo: "POST",
            autenticado: false,
            corpo: { email }
        });
        // O usuário pode ter mudado o e-mail enquanto a consulta estava em andamento
        if (campoEmail.value.trim() !== email) return;
        emailVerificado = email;
        if (resposta.situacao !== situacao) aplicarSituacao(resposta.situacao);
        else if (situacao === "novo") mostrarInfoEmail("");
    } catch (erro) {
        mostrarInfoEmail("Não foi possível verificar o e-mail.", "danger");
        mostrarAlerta(alerta, erro.message);
    }
}

function agendarVerificacao() {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => { consultaAtual = verificarEmail(); }, ESPERA_DIGITACAO);
}

campoEmail.addEventListener("input", agendarVerificacao);
campoEmail.addEventListener("change", () => {
    clearTimeout(temporizador);
    consultaAtual = verificarEmail();
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

    // Garante que o e-mail digitado por último já foi consultado
    clearTimeout(temporizador);
    await (consultaAtual = verificarEmail());
    if (situacao !== "novo" && situacao !== "sem_unidade") return;

    form.classList.add("was-validated");
    const idsUnidades = unidadesMarcadas();
    erroUnidades.hidden = idsUnidades.length > 0;
    if (!form.checkValidity() || idsUnidades.length === 0) return;

    const contaExistente = situacao === "sem_unidade";
    definirCarregando(botao, true, "Enviando...");
    try {
        const resposta = await api("/auth/cadastro", {
            metodo: "POST",
            autenticado: false,
            corpo: {
                // Conta existente: o nome já está cadastrado e a senha é a atual
                ...(contaExistente ? {} : { nome: form.nome.value.trim() }),
                email: campoEmail.value.trim(),
                senha: form.senha.value,
                ids_unidades: idsUnidades
            }
        });
        mostrarSucesso(contaExistente
            ? "Solicitação enviada! Você poderá entrar com o seu login assim que o síndico aprovar."
            : resposta.mensagem || "Cadastro enviado! Aguarde a aprovação do síndico.");
    } catch (erro) {
        // 409: e-mail de conta em uso (RN11) | 401: senha atual incorreta | 404: unidade não encontrada ou inativada
        // 400: unidades de condomínios diferentes
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
});

carregarCondominios();