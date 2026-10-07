// Validação do e-mail do síndico pelo link recebido (RN12)
import { api } from "../shared/api.js";
import { mostrarAlerta } from "../shared/ui.js";

const alerta = document.getElementById("alerta");
const carregando = document.getElementById("carregando");
const botaoLogin = document.getElementById("btn-login");

async function validar() {
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
        mostrarAlerta(alerta, "Link inválido. Peça ao administrador para reenviar o link de validação.");
        return;
    }

    try {
        const resposta = await api("/auth/validar-email", {
            metodo: "POST",
            autenticado: false,
            corpo: { token }
        });
        mostrarAlerta(alerta, resposta.mensagem, "success");
    } catch (erro) {
        // 400: link inválido, já utilizado ou expirado (válido por 2 dias)
        mostrarAlerta(alerta, `${erro.message} Se necessário, peça ao administrador para reenviar o link.`);
    }
}

await validar();
carregando.hidden = true;
botaoLogin.hidden = false;
