// 1.1 Tela de Login (RF01, RN12, RN13)
import { api, sessao } from "../shared/api.js";
import { rotaInicial } from "../shared/auth-guard.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";

const form = document.getElementById("form-login");
const botao = document.getElementById("btn-entrar");
const alerta = document.getElementById("alerta");

const MENSAGENS_MOTIVO = {
    sessao: ["Sua sessão expirou. Faça login novamente.", "warning"],
    pendente: ["Seu cadastro ainda está pendente de aprovação pelo síndico.", "warning"],
    senha: ["Senha redefinida com sucesso. Faça login com a nova senha.", "success"]
};

const MENSAGENS_VINCULO = {
    Pendente: "Seu cadastro ainda está pendente de aprovação pelo síndico. Você poderá entrar assim que ele for aprovado.",
    Rejeitado: "Sua solicitação de cadastro foi rejeitada pelo síndico. Procure a administração do condomínio."
};

// Mensagem vinda de um redirecionamento (ex.: ?motivo=sessao)
const motivo = new URLSearchParams(window.location.search).get("motivo");
if (MENSAGENS_MOTIVO[motivo]) {
    mostrarAlerta(alerta, ...MENSAGENS_MOTIVO[motivo]);
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    // Validação nativa do navegador com o visual do Bootstrap
    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    const email = form.email.value.trim();
    const senha = form.senha.value;

    definirCarregando(botao, true, "Entrando...");
    try {
        const resposta = await api("/auth/login", {
            metodo: "POST",
            corpo: { email, senha },
            autenticado: false
        });
        const usuario = resposta.usuario;

        // Morador sem vínculo aprovado: o login é válido, mas o sistema ainda não é liberado
        if (usuario.perfil === "Morador" && usuario.status_vinculo !== "Aprovado") {
            const mensagem = MENSAGENS_VINCULO[usuario.status_vinculo] || MENSAGENS_VINCULO.Pendente;
            mostrarAlerta(alerta, mensagem, "warning");
            return;
        }

        sessao.salvar(resposta.access_token, usuario);
        window.location.replace(rotaInicial(usuario));
    } catch (erro) {
        // 401: e-mail ou senha incorretos | 403: e-mail não validado (RN12) | 0: API fora do ar
        mostrarAlerta(alerta, erro.message);
        form.senha.value = "";
        form.classList.remove("was-validated");
    } finally {
        definirCarregando(botao, false);
    }
});
