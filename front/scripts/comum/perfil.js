// Tela Editar Perfil do morador (RF15)
// Nome e e-mail são editáveis; unidade e condomínio são só leitura.
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";

const usuario = await protegerPagina({ perfis: ["Morador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const form = document.getElementById("form-dados");
const campoNome = document.getElementById("nome");
const campoEmail = document.getElementById("email");
const botaoSalvar = document.getElementById("btn-salvar");

// Nome de um campo que pode vir como texto ou como objeto (ex.: { nome } ou { identificacao })
function nomeDe(valor) {
    if (!valor) return "";
    if (typeof valor === "string") return valor;
    return valor.identificacao || valor.nome || "";
}

async function carregarPerfil() {
    limparAlerta(alerta);
    try {
        // Dados atuais do usuário e unidades aprovadas dele
        const [dados, unidades] = await Promise.all([
            api("/auth/me"),
            api("/auth/me/unidades")
        ]);

        campoNome.value = dados.nome || usuario.nome || "";
        campoEmail.value = dados.email || usuario.email || "";
        document.getElementById("unidade").value =
            unidades.map((unidade) => unidade.identificacao).join(" · ") || "—";
        document.getElementById("condominio").value =
            nomeDe(dados.condominio) || nomeDe(usuario.condominio) || "—";

        // Libera a edição só depois de carregar
        campoNome.disabled = false;
        campoEmail.disabled = false;
        botaoSalvar.disabled = false;
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
    }
}

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    form.classList.add("was-validated");
    if (!form.checkValidity()) return;

    definirCarregando(botaoSalvar, true, "Salvando...");
    try {
        await api("/auth/me", {
            metodo: "PATCH",
            corpo: { nome: campoNome.value.trim(), email: campoEmail.value.trim() }
        });
        form.classList.remove("was-validated");
        // O nome no cabeçalho atualiza na próxima vez que uma tela for aberta
        mostrarAlerta(alerta, "Dados atualizados.", "success");
    } catch (erro) {
        // 400: e-mail já em uso por outra conta, ou dados inválidos
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botaoSalvar, false);
    }
});

await carregarPerfil();