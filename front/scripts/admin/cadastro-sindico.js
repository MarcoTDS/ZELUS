// 1.21 Tela de Cadastro de Síndico (RF13, RN07, RN12, RN13)
// Duas formas de definir o síndico do condomínio:
//   1) Pessoa nova: cria o usuário com senha provisória e link de validação.
//   2) Morador do condomínio: o link "Escolher entre os moradores" abre a lista e o morador escolhido é promovido.
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, mostrarAvisoPendente, escaparHtml, confirmar } from "../shared/ui.js";
import { mostrarAcessoSindico } from "./acesso-sindico.js";

const usuario = await protegerPagina({ perfis: ["Administrador"] });
montarCabecalho(usuario);

const $ = (id) => document.getElementById(id);
const form = $("form-sindico");
const alerta = $("alerta");
const botaoCadastrar = $("btn-cadastrar");
const botaoReenviar = $("btn-reenviar");
const resultado = $("resultado");
const acessoSindico = $("acesso-sindico");
const selectCondominio = form.condominio;

const avisoMoradores = $("aviso-moradores");
const camposNovo = $("campos-novo");
const camposPromover = $("campos-promover");
const listaMoradores = $("lista-moradores");
const buscaMorador = $("busca-morador");
const erroMorador = $("erro-morador");

// Vem preenchido quando o admin acabou de cadastrar o condomínio ou clicou em "Cadastrar síndico" na lista
const condominioSugerido = new URLSearchParams(window.location.search).get("condominio");
let idSindicoCadastrado = null;

// Moradores do condomínio escolhido e o modo da tela ("novo" ou "promover")
let moradores = [];
let modo = "novo";
let consultaAtual = 0; // descarta respostas atrasadas quando o admin troca de condomínio rápido

mostrarAvisoPendente(alerta);

// ==========================================
// CONDOMÍNIOS
// ==========================================
async function carregarCondominios() {
    try {
        // RN07: cada condomínio tem exatamente um síndico, então só listamos os que ainda não têm
        const condominios = (await api("/admin/condominios")).filter((c) => !c.id_sindico);

        selectCondominio.innerHTML = "";
        if (!condominios.length) {
            selectCondominio.add(new Option("Nenhum condomínio sem síndico", ""));
            selectCondominio.disabled = true;
            botaoCadastrar.disabled = true;
            mostrarAlerta(alerta, "Todos os condomínios ativos já têm síndico. Cadastre um condomínio novo primeiro.", "info");
            return;
        }

        selectCondominio.add(new Option("Selecione o condomínio", ""));
        for (const c of condominios) {
            selectCondominio.add(new Option(`${c.nome} (${c.cidade}/${c.estado})`, c.id));
        }
        if (condominioSugerido) {
            selectCondominio.value = condominioSugerido;
            await carregarMoradores();
        }
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

// ==========================================
// MORADORES (promoção a síndico)
// ==========================================
function definirModo(novoModo) {
    modo = novoModo;
    const promover = modo === "promover";

    // fieldset desabilitado não é validado nem enviado: só um dos dois grupos vale por vez
    camposNovo.hidden = promover;
    camposNovo.disabled = promover;
    camposPromover.hidden = !promover;
    camposPromover.disabled = !promover;
    avisoMoradores.hidden = promover || moradores.length === 0;
    erroMorador.hidden = true;
    botaoCadastrar.textContent = promover ? "Promover a Síndico" : "Cadastrar Síndico";
    form.classList.remove("was-validated");

    if (promover) {
        buscaMorador.value = "";
        desenharMoradores();
    }
}

function textoBusca(morador) {
    return [morador.nome, morador.email, ...morador.unidades].join(" ").toLowerCase();
}

function desenharMoradores() {
    const termo = buscaMorador.value.trim().toLowerCase();
    const escolhido = listaMoradores.querySelector("input:checked")?.value;
    const visiveis = moradores.filter((m) => !termo || textoBusca(m).includes(termo));

    // Busca só faz sentido com lista maior
    buscaMorador.hidden = moradores.length <= 5;

    if (!visiveis.length) {
        listaMoradores.innerHTML = `<p class="small texto-suave mb-0">Nenhum morador encontrado.</p>`;
        return;
    }

    listaMoradores.innerHTML = visiveis.map((m) => `
        <label class="opcao-morador">
            <input class="form-check-input" type="radio" name="morador" value="${m.id}" ${String(m.id) === escolhido ? "checked" : ""}>
            <span>
                <span class="d-block fw-semibold">${escaparHtml(m.nome)}</span>
                <span class="d-block small detalhe">${escaparHtml(m.email)}</span>
                <span class="d-block small detalhe">${m.unidades.map(escaparHtml).join(" · ")}</span>
            </span>
        </label>`).join("");
}

async function carregarMoradores() {
    const consulta = ++consultaAtual;
    moradores = [];
    avisoMoradores.hidden = true;
    if (!selectCondominio.value) {
        definirModo("novo");
        return;
    }

    try {
        const lista = await api(`/admin/condominios/${encodeURIComponent(selectCondominio.value)}/moradores`);
        if (consulta !== consultaAtual) return;
        moradores = lista;
    } catch (erro) {
        if (consulta !== consultaAtual) return;
        mostrarAlerta(alerta, erro.message);
    }

    $("texto-moradores").textContent = moradores.length === 1
        ? "Este condomínio já tem 1 morador cadastrado."
        : `Este condomínio já tem ${moradores.length} moradores cadastrados.`;

    // Trocou para um condomínio sem moradores: volta ao cadastro de pessoa nova
    definirModo(modo === "promover" && moradores.length ? "promover" : "novo");
}

selectCondominio.addEventListener("change", () => {
    limparAlerta(alerta);
    carregarMoradores();
});

$("link-moradores").addEventListener("click", (evento) => {
    evento.preventDefault();
    definirModo("promover");
});

$("link-pessoa-nova").addEventListener("click", (evento) => {
    evento.preventDefault();
    definirModo("novo");
});

buscaMorador.addEventListener("input", desenharMoradores);
listaMoradores.addEventListener("change", () => { erroMorador.hidden = true; });

// ==========================================
// ENVIO
// ==========================================
function mostrarResultado(acesso) {
    idSindicoCadastrado = acesso.id_usuario;
    form.hidden = true;
    resultado.hidden = false;
    mostrarAcessoSindico(acessoSindico, acesso);

    // Morador promovido já tem e-mail validado e senha própria: não há link para reenviar
    botaoReenviar.hidden = Boolean(acesso.promovido);
    $("titulo-resultado").textContent = acesso.promovido ? "Morador Promovido a Síndico" : "Síndico Cadastrado";
}

async function promoverMorador() {
    const escolhido = listaMoradores.querySelector("input:checked");
    if (!escolhido) {
        erroMorador.hidden = false;
        return;
    }
    const morador = moradores.find((m) => String(m.id) === escolhido.value);
    const condominio = selectCondominio.selectedOptions[0].text;

    if (!(await confirmar({
        titulo: "Promover a síndico?",
        mensagem: `${morador.nome} passará a ser o síndico de ${condominio}, com o mesmo login e senha.\n\nEnquanto for síndico, ele acompanha a fila de chamados e não aparece mais na lista de moradores.`,
        textoConfirmar: "Promover a síndico",
        perigo: false
    }))) return;

    definirCarregando(botaoCadastrar, true, "Promovendo...");
    try {
        const acesso = await api("/admin/sindicos/promover", {
            metodo: "POST",
            corpo: { id_condominio: Number(selectCondominio.value), id_usuario: morador.id }
        });
        mostrarAlerta(alerta, `${morador.nome} agora é o síndico de ${condominio}.`, "success");
        mostrarResultado(acesso);
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botaoCadastrar, false);
    }
}

async function cadastrarPessoaNova() {
    definirCarregando(botaoCadastrar, true, "Cadastrando...");
    try {
        const acesso = await api("/admin/sindicos", {
            metodo: "POST",
            corpo: {
                id_condominio: Number(selectCondominio.value),
                nome: form.nome.value.trim(),
                email: form.email.value.trim()
            }
        });
        const condominio = selectCondominio.selectedOptions[0].text;
        mostrarAlerta(alerta, `Síndico cadastrado e vinculado a ${condominio}.`, "success");
        mostrarResultado(acesso);
    } catch (erro) {
        // 409: condomínio já tem síndico (RN07) ou e-mail já cadastrado
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botaoCadastrar, false);
    }
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    if (modo === "promover") await promoverMorador();
    else await cadastrarPessoaNova();
});

botaoReenviar.addEventListener("click", async () => {
    limparAlerta(alerta);
    definirCarregando(botaoReenviar, true, "Reenviando...");
    try {
        // Gera um novo link e uma nova senha provisória (os anteriores deixam de valer)
        const acesso = await api(`/admin/sindicos/${idSindicoCadastrado}/reenviar-validacao`, { metodo: "POST" });
        mostrarAcessoSindico(acessoSindico, acesso);
        mostrarAlerta(alerta, "Novo link e nova senha provisória gerados. Os anteriores deixaram de valer.", "info");
    } catch (erro) {
        // 400: o síndico já validou o e-mail
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botaoReenviar, false);
    }
});

carregarCondominios();
