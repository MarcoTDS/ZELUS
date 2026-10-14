// Tela Abrir Chamado (RF07, RN05, RN09)
import { api } from "../shared/api.js";
import { protegerPagina } from "../shared/auth-guard.js";
import { montarCabecalho } from "../shared/layout.js";
import { mostrarAlerta, limparAlerta, definirCarregando } from "../shared/ui.js";
import { ROTAS } from "../shared/config.js";

const usuario = await protegerPagina({ perfis: ["Morador"] });
montarCabecalho(usuario);

const alerta = document.getElementById("alerta");
const form = document.getElementById("form-chamado");
const selectCategoria = document.getElementById("categoria");
const selectUnidade = document.getElementById("unidade");
const avisoDuplicidade = document.getElementById("aviso-duplicidade");
const btnEnviar = document.getElementById("btn-enviar");

// Troca as opções de um select por um único texto (ex.: "Carregando...")
function mostrarTexto(select, texto) {
    select.innerHTML = "";
    const opcao = document.createElement("option");
    opcao.value = "";
    opcao.textContent = texto;
    opcao.selected = true;
    opcao.disabled = true;
    select.appendChild(opcao);
    select.disabled = true;
}

// Preenche um select com os itens da API; "rotulo" diz qual campo mostrar
function preencher(select, itens, textoInicial, rotulo) {
    mostrarTexto(select, textoInicial);
    itens.forEach((item) => {
        const opcao = document.createElement("option");
        opcao.value = item.id;
        opcao.textContent = rotulo(item);
        select.appendChild(opcao);
    });
    select.disabled = false;
    // Só uma opção: já deixa escolhida
    if (itens.length === 1) select.value = String(itens[0].id);
}

async function carregarLista(select, rota, textoInicial, textoVazio, rotulo) {
    try {
        const itens = await api(rota);
        if (itens.length === 0) mostrarTexto(select, textoVazio);
        else preencher(select, itens, textoInicial, rotulo);
    } catch (erro) {
        mostrarTexto(select, "Não foi possível carregar");
        mostrarAlerta(alerta, erro.message);
    }
}

// RN09: aviso de chamado parecido (não bloqueia o envio)
async function verificarSimilaridade() {
    avisoDuplicidade.classList.add("d-none");
    if (!selectCategoria.value || !selectUnidade.value) return;

    try {
        const resultado = await api(
            `/chamados/similaridade?id_categoria=${encodeURIComponent(selectCategoria.value)}` +
            `&id_unidade=${encodeURIComponent(selectUnidade.value)}`
        );
        if (resultado.existe_similar) avisoDuplicidade.classList.remove("d-none");
    } catch (erro) {
        // Se a verificação falhar, segue sem aviso
    }
}

selectCategoria.addEventListener("change", verificarSimilaridade);
selectUnidade.addEventListener("change", verificarSimilaridade);

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        return;
    }

    const corpo = {
        titulo: document.getElementById("titulo").value.trim(),
        descricao: document.getElementById("descricao").value.trim(),
        id_categoria: Number(selectCategoria.value),
        id_unidade_destino: Number(selectUnidade.value)
    };
    const foto = document.getElementById("link-foto").value.trim();
    const video = document.getElementById("link-video").value.trim();
    if (foto) corpo.foto_url = foto;
    if (video) corpo.video_url = video;

    definirCarregando(btnEnviar, true, "Enviando...");
    try {
        const resposta = await api("/chamados/", { metodo: "POST", corpo });
        // Abre o chamado recém-criado
        window.location.href = `${ROTAS.comum.chamado}?id=${encodeURIComponent(resposta.chamado.id)}&novo=1`;
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(btnEnviar, false);
    }
});

// Ao abrir a tela: categorias ativas e unidades que o morador pode usar (RN05)
await Promise.all([
    carregarLista(selectCategoria, "/categorias/", "Selecione a categoria", "Nenhuma categoria cadastrada", (c) => c.nome),
    carregarLista(selectUnidade, "/unidades/para-chamado", "Selecione a unidade", "Nenhuma unidade disponível", (u) => u.identificacao || u.nome)
]);