// Tela Abrir Chamado (RF07, RN05, RN09), com 1 foto e 1 vídeo opcionais
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

const MB = 1024 * 1024;
const LIMITE_FOTO = 5 * MB;
const LIMITE_VIDEO = 50 * MB;
const FORMATOS_FOTO = ["image/jpeg", "image/png", "image/webp"];
const LADO_MAXIMO_FOTO = 1600; // px: suficiente para ver o problema, e a foto de 4 MB do celular cai para ~300 KB

// Arquivos prontos para envio e quais já foram enviados (se um envio falhar, só ele é repetido)
const anexos = { foto: null, video: null };
const enviados = { foto: false, video: false };
const NOMES_ANEXO = { foto: "a foto", video: "o vídeo" };

// Chamado já criado nesta tela (quando o envio de um anexo falha, não cria outro chamado ao tentar de novo)
let idChamadoCriado = null;
let preparandoFoto = Promise.resolve();
const linkPularAnexo = document.getElementById("link-pular-anexo");

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

// ==========================================
// ANEXOS
// ==========================================
// Reduz a foto no próprio navegador (canvas). Se o navegador não conseguir ler o arquivo
// (ex.: HEIC no Chrome), manda o original e a API confere o formato.
async function reduzirFoto(arquivo) {
    try {
        const imagem = await createImageBitmap(arquivo);
        const escala = Math.min(1, LADO_MAXIMO_FOTO / Math.max(imagem.width, imagem.height));
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(imagem.width * escala);
        canvas.height = Math.round(imagem.height * escala);
        canvas.getContext("2d").drawImage(imagem, 0, 0, canvas.width, canvas.height);
        imagem.close();

        const reduzida = await new Promise((resolver) => canvas.toBlob(resolver, "image/jpeg", 0.82));
        if (!reduzida || (reduzida.size >= arquivo.size && FORMATOS_FOTO.includes(arquivo.type))) return arquivo;
        return new File([reduzida], "foto.jpg", { type: "image/jpeg" });
    } catch {
        return arquivo;
    }
}

function mostrarErroAnexo(tipo, mensagem) {
    const campo = document.getElementById(`arquivo-${tipo}`);
    document.getElementById(`erro-${tipo}`).textContent = mensagem;
    campo.setCustomValidity(mensagem);
    campo.classList.toggle("is-invalid", Boolean(mensagem));
}

function mostrarPrevia(tipo, arquivo) {
    const previa = document.getElementById(`previa-${tipo}`);
    if (previa.src) URL.revokeObjectURL(previa.src);
    if (arquivo) previa.src = URL.createObjectURL(arquivo);
    else previa.removeAttribute("src");
    document.getElementById(`bloco-previa-${tipo}`).classList.toggle("d-none", !arquivo);
}

// Ao escolher outro arquivo, descarta o anterior (o campo continua mostrando o nome do novo)
function limparEscolha(tipo) {
    anexos[tipo] = null;
    enviados[tipo] = false;
    mostrarErroAnexo(tipo, "");
    mostrarPrevia(tipo, null);
}

function removerAnexo(tipo) {
    document.getElementById(`arquivo-${tipo}`).value = "";
    limparEscolha(tipo);
}

async function escolherFoto() {
    const original = document.getElementById("arquivo-foto").files[0];
    limparEscolha("foto");
    if (!original) return;

    if (original.type && !original.type.startsWith("image/")) {
        mostrarErroAnexo("foto", "Escolha um arquivo de imagem.");
        return;
    }
    const foto = await reduzirFoto(original);
    if (!FORMATOS_FOTO.includes(foto.type)) {
        mostrarErroAnexo("foto", "Formato não aceito. Use JPG, PNG ou WEBP.");
    } else if (foto.size > LIMITE_FOTO) {
        mostrarErroAnexo("foto", "A foto deve ter no máximo 5 MB.");
    } else {
        anexos.foto = foto;
        mostrarPrevia("foto", foto);
    }
}

function escolherVideo() {
    const video = document.getElementById("arquivo-video").files[0];
    limparEscolha("video");
    if (!video) return;
    if (video.type && !video.type.startsWith("video/")) {
        mostrarErroAnexo("video", "Escolha um arquivo de vídeo.");
    } else if (video.size > LIMITE_VIDEO) {
        mostrarErroAnexo("video", `O vídeo tem ${(video.size / MB).toFixed(0)} MB. O máximo é 50 MB: grave um vídeo mais curto.`);
    } else {
        anexos.video = video;
        mostrarPrevia("video", video);
    }
}

document.getElementById("arquivo-foto").addEventListener("change", () => { preparandoFoto = escolherFoto(); });
document.getElementById("arquivo-video").addEventListener("change", escolherVideo);
document.getElementById("remover-foto").addEventListener("click", () => removerAnexo("foto"));
document.getElementById("remover-video").addEventListener("click", () => removerAnexo("video"));

async function enviarAnexo(tipo) {
    const dados = new FormData();
    dados.append("arquivo", anexos[tipo], anexos[tipo].name);
    await api(`/chamados/${encodeURIComponent(idChamadoCriado)}/anexos/${tipo}`, { metodo: "POST", corpo: dados });
    enviados[tipo] = true;
}

// Depois de criado, título, descrição, categoria e unidade não mudam mais nesta tela
function travarDadosDoChamado() {
    ["titulo", "descricao"].forEach((id) => { document.getElementById(id).readOnly = true; });
    selectCategoria.disabled = true;
    selectUnidade.disabled = true;
}

selectCategoria.addEventListener("change", verificarSimilaridade);
selectUnidade.addEventListener("change", verificarSimilaridade);

function abrirChamadoCriado() {
    window.location.href = `${ROTAS.comum.chamado}?id=${encodeURIComponent(idChamadoCriado)}&novo=1`;
}

linkPularAnexo.addEventListener("click", (evento) => {
    evento.preventDefault();
    abrirChamadoCriado();
});

form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparAlerta(alerta);

    await preparandoFoto; // a foto pode ainda estar sendo reduzida
    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        return;
    }

    definirCarregando(btnEnviar, true, "Enviando...");
    try {
        if (!idChamadoCriado) {
            const resposta = await api("/chamados/", {
                metodo: "POST",
                corpo: {
                    titulo: document.getElementById("titulo").value.trim(),
                    descricao: document.getElementById("descricao").value.trim(),
                    id_categoria: Number(selectCategoria.value),
                    id_unidade_destino: Number(selectUnidade.value)
                }
            });
            idChamadoCriado = resposta.chamado.id;
            travarDadosDoChamado();
        }
    } catch (erro) {
        mostrarAlerta(alerta, erro.message);
        definirCarregando(btnEnviar, false);
        return;
    }

    // O chamado já existe: agora vão os anexos, um de cada vez
    for (const tipo of ["foto", "video"]) {
        if (!anexos[tipo] || enviados[tipo]) continue;
        definirCarregando(btnEnviar, false);
        definirCarregando(btnEnviar, true, tipo === "foto" ? "Enviando foto..." : "Enviando vídeo...");
        try {
            await enviarAnexo(tipo);
        } catch (erro) {
            mostrarAlerta(alerta,
                `O chamado #${idChamadoCriado} foi aberto, mas ${NOMES_ANEXO[tipo]} não foi enviado: ${erro.message} ` +
                "Troque o arquivo ou tente de novo.", "warning");
            definirCarregando(btnEnviar, false);
            btnEnviar.textContent = "Tentar enviar o anexo";
            linkPularAnexo.classList.remove("d-none");
            return;
        }
    }

    abrirChamadoCriado();
});

// Ao abrir a tela: categorias ativas e unidades que o morador pode usar (RN05)
await Promise.all([
    carregarLista(selectCategoria, "/categorias/", "Selecione a categoria", "Nenhuma categoria cadastrada", (c) => c.nome),
    carregarLista(selectUnidade, "/unidades/para-chamado", "Selecione a unidade", "Nenhuma unidade disponível", (u) => u.identificacao || u.nome)
]);