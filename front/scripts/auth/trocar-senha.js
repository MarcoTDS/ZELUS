// 1.17 Tela Trocar Senha - 1º Acesso (RF16, RN13)
import { api, sessao } from "../shared/api.js";
import { protegerPagina, rotaInicial, sair } from "../shared/auth-guard.js";
import { mostrarAlerta, limparAlerta, definirCarregando, vincularConfirmacaoSenha } from "../shared/ui.js";

const form = document.getElementById("form-senha");
const botao = document.getElementById("btn-definir");
const alerta = document.getElementById("alerta");
const confirmacao = form.confirmar_nova_senha;

document.getElementById("link-sair").addEventListener("click", (evento) => {
    evento.preventDefault();
    sair();
});

// Única tela liberada enquanto a senha provisória não for trocada
const usuario = await protegerPagina({ permitirSenhaProvisoria: true });

// Quem já trocou a senha usa a tela "Alterar Senha" (1.18), não esta
if (!usuario.senha_provisoria) {
    window.location.replace(rotaInicial(usuario));
}

// Confere a confirmação enquanto o usuário digita
const validarConfirmacao = vincularConfirmacaoSenha(form.nova_senha, confirmacao);

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    validarConfirmacao();
    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botao, true, "Salvando...");
    try {
        await api("/auth/me/senha", {
            metodo: "PATCH",
            corpo: {
                senha_atual: form.senha_atual.value,
                nova_senha: form.nova_senha.value,
                confirmar_nova_senha: confirmacao.value
            }
        });

        // RN13: a partir daqui o restante do sistema fica liberado
        const atualizado = { ...usuario, senha_provisoria: false };
        sessao.salvarUsuario(atualizado);
        window.location.replace(rotaInicial(atualizado));
    } catch (erro) {
        // 400: senha provisória incorreta ou nova senha igual à atual
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botao, false);
    }
});
