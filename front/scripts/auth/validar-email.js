// Validação do e-mail do síndico pelo link recebido (RN12).
// O link traz o código: validar-email.html?token=abc123  ->  POST /auth/validar-email
import { api } from "../shared/api.js";

const token = new URLSearchParams(window.location.search).get("token");

const ESTADOS = ["estadoValidando", "estadoSucesso", "estadoErro"];

function mostrar(estado) {
    for (const id of ESTADOS) {
        document.getElementById(id).classList.toggle("d-none", id !== estado);
    }
}

function mostrarErro(titulo, texto) {
    document.getElementById("tituloErro").textContent = titulo;
    document.getElementById("textoErro").textContent = texto;
    mostrar("estadoErro");
}

// A API responde 400 com a mensagem do motivo; o título é escolhido pelo texto dela
function tituloDoErro(mensagem) {
    const texto = mensagem.toLowerCase();
    if (texto.includes("já") && texto.includes("valid")) return "E-mail já validado";
    if (texto.includes("expir")) return "Link expirado";
    return "Link inválido";
}

async function validar() {
    if (!token) {
        mostrarErro("Link incompleto",
            "Não encontramos o código de validação neste link. Abra novamente o link que foi enviado para o seu e-mail.");
        return;
    }

    try {
        await api("/auth/validar-email", {
            metodo: "POST",
            autenticado: false,
            corpo: { token }
        });
        mostrar("estadoSucesso");
    } catch (erro) {
        if (erro.status === 0) {
            mostrarErro("Não foi possível validar",
                "Tivemos um problema para falar com o servidor. Tente abrir o link de novo em alguns instantes.");
            return;
        }
        mostrarErro(tituloDoErro(erro.message), erro.message);
    }
}

validar();