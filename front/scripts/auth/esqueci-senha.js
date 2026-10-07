// 1.2 Tela "Esqueci a Senha" (RF19, RN16)
import { api } from "../shared/api.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";

const form = document.getElementById("form-esqueci");
const botao = document.getElementById("btn-enviar");
const alerta = document.getElementById("alerta");

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botao, true, "Enviando...");
    try {
        // A API responde sempre a mesma mensagem, exista ou não o e-mail (não revela contas cadastradas)
        const resposta = await api("/auth/esqueci-senha", {
            metodo: "POST",
            autenticado: false,
            corpo: { email: form.email.value.trim() }
        });
        mostrarAlerta(alerta, resposta.mensagem, "success");
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botao, false);
    }
});
