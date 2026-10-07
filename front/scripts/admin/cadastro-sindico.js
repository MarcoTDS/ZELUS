// 1.21 Tela de Cadastro de Síndico (RF13, RN07, RN12, RN13)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando, mostrarAvisoPendente } from "../shared/ui.js";
import { mostrarAcessoSindico } from "./acesso-sindico.js";

const usuario = await protegerPagina({ perfis: ["Administrador"] });
montarCabecalho(usuario);

const form = document.getElementById("form-sindico");
const alerta = document.getElementById("alerta");
const botaoCadastrar = document.getElementById("btn-cadastrar");
const botaoReenviar = document.getElementById("btn-reenviar");
const resultado = document.getElementById("resultado");
const acessoSindico = document.getElementById("acesso-sindico");
const selectCondominio = form.condominio;

// Vem preenchido quando o admin acabou de cadastrar o condomínio ou clicou em "Cadastrar síndico" na lista
const condominioSugerido = new URLSearchParams(window.location.search).get("condominio");
let idSindicoCadastrado = null;

mostrarAvisoPendente(alerta);

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
        if (condominioSugerido) selectCondominio.value = condominioSugerido;
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

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
        idSindicoCadastrado = acesso.id_usuario;

        const condominio = selectCondominio.selectedOptions[0].text;
        mostrarAlerta(alerta, `Síndico cadastrado e vinculado a ${condominio}.`, "success");
        form.hidden = true;
        resultado.hidden = false;
        mostrarAcessoSindico(acessoSindico, acesso);
    } catch (erro) {
        // 409: condomínio já tem síndico (RN07) ou e-mail já cadastrado
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botaoCadastrar, false);
    }
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
