// Tela Editar Perfil (RF15), para morador e síndico.
// Só o nome é editável; e-mail, unidade e condomínio ficam bloqueados (só leitura).
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";
import { ROTAS } from "../shared/config.js";

const usuario = await protegerPagina({ perfis: ["Morador", "Sindico"] });
montarCabecalho(usuario);

const ehSindico = usuario.perfil === "Sindico";
document.getElementById("link-voltar").href = ROTAS.inicio[usuario.perfil];
document.getElementById("rotulo-perfil").textContent = ehSindico ? "Síndico" : "Morador";
if (ehSindico) {
    document.getElementById("aviso-bloqueado").textContent = "Só o nome pode ser alterado. Para trocar o e-mail, a unidade ou o condomínio, fale com o administrador.";
}

const alerta = document.getElementById("alerta");
const form = document.getElementById("form-dados");
const campoNome = document.getElementById("nome");
const campoEmail = document.getElementById("email"); // só leitura
const botaoSalvar = document.getElementById("btn-salvar");

// A API de /auth/me devolve só o id do condomínio; o nome vem da lista pública de condomínios
async function buscarNomeCondominio(idCondominio) {
    if (!idCondominio) return "—";
    try {
        const condominios = await api("/publico/condominios", { autenticado: false });
        return condominios.find((c) => c.id === idCondominio)?.nome || "—";
    } catch {
        return "—";
    }
}

async function carregarPerfil() {
    limparAlerta(alerta);
    try {
        // Dados atuais do usuário e unidades aprovadas dele
        // (síndico promovido a partir de morador continua com a unidade; síndico comum não tem nenhuma)
        const dados = await api("/auth/me");
        const unidades = await api("/auth/me/unidades");

        // Sem unidade (síndico comum): só o condomínio aparece
        const semUnidade = unidades.length === 0;
        document.getElementById("grupo-unidade").hidden = ehSindico && semUnidade;
        document.getElementById("grupo-condominio").className = ehSindico && semUnidade ? "col-12" : "col-md-6";

        campoNome.value = dados.nome || usuario.nome || "";
        campoEmail.value = dados.email || usuario.email || "";
        document.getElementById("unidade").value =
            unidades.map((unidade) => unidade.identificacao).join(" · ") || "—";
        document.getElementById("condominio").value = await buscarNomeCondominio(dados.id_condominio ?? usuario.id_condominio);

        // Libera a edição só depois de carregar
        campoNome.disabled = false;
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
            corpo: { nome: campoNome.value.trim() }
        });
        form.classList.remove("was-validated");
        // O nome no cabeçalho atualiza na próxima vez que uma tela for aberta
        mostrarAlerta(alerta, "Dados atualizados.", "success");
    } catch (erro) {
        // 400: dados inválidos
        mostrarAlerta(alerta, erro.message);
    } finally {
        definirCarregando(botaoSalvar, false);
    }
});

await carregarPerfil();