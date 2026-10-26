// Tela Alterar Senha (RF15, RF16) — usada por todos os perfis.
// Troca a senha do usuário logado. (O primeiro acesso com senha provisória usa a trocar-senha.js.)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { ROTAS } from "../shared/config.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Morador", "Sindico", "Administrador"] });
montarCabecalho(usuario);

const NOMES_PERFIL = { Morador: "Morador", Sindico: "Síndico", Administrador: "Administrador" };

const alerta = document.getElementById("alerta");
const form = document.getElementById("form-senha");
const atual = document.getElementById("senhaAtual");
const nova = document.getElementById("novaSenha");
const confirmar = document.getElementById("confirmarSenha");
const erroNova = document.getElementById("erroNovaSenha");
const botaoSalvar = document.getElementById("btn-salvar");
const botaoMostrar = document.getElementById("mostrarSenhas");

// ==========================================
// AJUSTES POR PERFIL
// ==========================================
document.getElementById("rotulo-perfil").textContent = NOMES_PERFIL[usuario.perfil] || usuario.perfil;
document.getElementById("link-voltar").href = ROTAS.inicio[usuario.perfil];

// ==========================================
// REQUISITOS DA SENHA
// ==========================================
function regras() {
    return {
        tamanho: nova.value.length >= 8,
        diferente: nova.value.length > 0 && nova.value !== atual.value
    };
}

function validarSenha() {
    const r = regras();

    document.querySelectorAll("#requisitos li").forEach((li) => {
        li.classList.toggle("ok", r[li.dataset.regra]);
    });

    if (!r.tamanho) {
        nova.setCustomValidity("curta");
        erroNova.textContent = "A senha precisa ter pelo menos 8 caracteres.";
    } else if (!r.diferente) {
        nova.setCustomValidity("igual");
        erroNova.textContent = "A nova senha precisa ser diferente da atual.";
    } else {
        nova.setCustomValidity("");
    }

    confirmar.setCustomValidity(confirmar.value && confirmar.value === nova.value ? "" : "diferente");
}

[atual, nova, confirmar].forEach((campo) => campo.addEventListener("input", validarSenha));

botaoMostrar.addEventListener("click", () => {
    const mostrar = atual.type === "password";
    [atual, nova, confirmar].forEach((campo) => { campo.type = mostrar ? "text" : "password"; });
    botaoMostrar.textContent = mostrar ? "Ocultar senhas" : "Mostrar senhas";
});

// ==========================================
// ENVIO
// ==========================================
form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);
    validarSenha();

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botaoSalvar, true, "Salvando...");
    try {
        await api("/auth/me/senha", {
            metodo: "PATCH",
            corpo: {
                senha_atual: atual.value,
                nova_senha: nova.value,
                confirmar_nova_senha: confirmar.value
            }
        });

        form.reset();
        form.classList.remove("was-validated");
        document.querySelectorAll("#requisitos li").forEach((li) => li.classList.remove("ok"));
        mostrarAlerta(alerta, "Senha alterada! Use a nova senha no próximo login.", "success");
    } catch (erro) {
        // 400: senha atual incorreta ou nova senha igual à atual
        mostrarAlerta(alerta, erro.message);
        atual.focus();
    } finally {
        definirCarregando(botaoSalvar, false);
    }
});