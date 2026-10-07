// Redefinir senha pelo link do e-mail (RF19, RN16)
import { api } from "../shared/api.js";
import { ROTAS } from "../shared/config.js";
import { mostrarAlerta, limparAlerta, definirCarregando, vincularConfirmacaoSenha } from "../shared/ui.js";

const form = document.getElementById("form-redefinir");
const botao = document.getElementById("btn-redefinir");
const alerta = document.getElementById("alerta");
const confirmacao = form.confirmar_nova_senha;

const token = new URLSearchParams(window.location.search).get("token");

// Sem token na URL não há o que redefinir
if (!token) {
    form.hidden = true;
    mostrarAlerta(alerta, "Link inválido. Solicite um novo link de redefinição de senha.");
}

const validarConfirmacao = vincularConfirmacaoSenha(form.nova_senha, confirmacao);

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    validarConfirmacao();
    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botao, true, "Salvando...");
    try {
        await api("/auth/redefinir-senha", {
            metodo: "POST",
            autenticado: false,
            corpo: {
                token,
                nova_senha: form.nova_senha.value,
                confirmar_nova_senha: confirmacao.value
            }
        });
        window.location.replace(`${ROTAS.login}?motivo=senha`);
    } catch (erro) {
        // 400: link inválido, já utilizado ou expirado (válido por 1 hora)
        mostrarAlerta(alerta, erro.message);
        definirCarregando(botao, false);
    }
});
