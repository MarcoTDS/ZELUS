// Pequenos utilitários de interface reutilizados pelas telas.

// Exibe uma mensagem (alert do Bootstrap) dentro do elemento informado.
// tipo: "danger" | "success" | "warning" | "info"
export function mostrarAlerta(container, mensagem, tipo = "danger") {
    container.innerHTML = "";
    const alerta = document.createElement("div");
    alerta.className = `alert alert-${tipo} py-2 mb-3`;
    alerta.setAttribute("role", "alert");
    alerta.textContent = mensagem; // textContent evita injeção de HTML
    container.appendChild(alerta);
}

export function limparAlerta(container) {
    container.innerHTML = "";
}

// Liga os campos "Nova senha" e "Confirmar nova senha": marca a confirmação como inválida enquanto não conferir.
// Devolve a função de validação, para ser chamada também no envio do formulário.
export function vincularConfirmacaoSenha(campoSenha, campoConfirmacao) {
    const validar = () => {
        const confere = campoConfirmacao.value === campoSenha.value;
        campoConfirmacao.setCustomValidity(confere ? "" : "A confirmação não confere.");
    };
    campoSenha.addEventListener("input", validar);
    campoConfirmacao.addEventListener("input", validar);
    return validar;
}

// Desabilita o botão e mostra um spinner enquanto a requisição está em andamento.
export function definirCarregando(botao, carregando, textoCarregando = "Aguarde...") {
    if (carregando) {
        botao.dataset.textoOriginal = botao.innerHTML;
        botao.disabled = true;
        botao.innerHTML = `<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>${textoCarregando}`;
    } else {
        botao.disabled = false;
        botao.innerHTML = botao.dataset.textoOriginal || botao.innerHTML;
    }
}

// ==========================================
// JANELA DE CONFIRMAÇÃO
// ==========================================
// Substitui o confirm() do navegador por uma janela no centro da tela, no padrão do sistema.
// Uso: if (!(await confirmar({ titulo: "Inativar?", mensagem: "...", textoConfirmar: "Inativar" }))) return;
// Devolve true se a pessoa confirmou, false se cancelou ou fechou a janela.
// "perigo" deixa o botão de confirmar vermelho (ações que bloqueiam, removem ou travam algo).
let janelaConfirmacao = null;

function montarJanelaConfirmacao() {
    if (janelaConfirmacao) return janelaConfirmacao;

    document.body.insertAdjacentHTML("beforeend", `
        <div class="modal fade" id="modal-confirmar" tabindex="-1" aria-labelledby="titulo-confirmar" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0 pb-0">
                        <h2 class="modal-title h5 fw-semibold" id="titulo-confirmar"></h2>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
                    </div>
                    <div class="modal-body">
                        <p class="small texto-suave mb-0" id="mensagem-confirmar" style="white-space: pre-line;"></p>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <button type="button" class="btn btn-outline-secondary" id="btn-cancelar-confirmar" data-bs-dismiss="modal"></button>
                        <button type="button" class="btn" id="btn-confirmar-confirmar"></button>
                    </div>
                </div>
            </div>
        </div>`);

    const elemento = document.getElementById("modal-confirmar");
    janelaConfirmacao = { elemento, modal: new bootstrap.Modal(elemento) };
    return janelaConfirmacao;
}

export function confirmar({ titulo, mensagem, textoConfirmar = "Confirmar", textoCancelar = "Cancelar", perigo = true }) {
    const { elemento, modal } = montarJanelaConfirmacao();

    elemento.querySelector("#titulo-confirmar").textContent = titulo;
    elemento.querySelector("#mensagem-confirmar").textContent = mensagem;
    elemento.querySelector("#btn-cancelar-confirmar").textContent = textoCancelar;
    const botao = elemento.querySelector("#btn-confirmar-confirmar");
    botao.textContent = textoConfirmar;
    botao.className = `btn ${perigo ? "btn-danger" : "btn-zelus"}`;

    return new Promise((resolver) => {
        let confirmado = false;
        botao.onclick = () => { confirmado = true; modal.hide(); };
        elemento.addEventListener("hidden.bs.modal", () => resolver(confirmado), { once: true });
        modal.show();
    });
}

// Escapa textos vindos da API antes de montar HTML com template strings (evita injeção de HTML)
export function escaparHtml(texto) {
    const div = document.createElement("div");
    div.textContent = texto ?? "";
    return div.innerHTML;
}

// ==========================================
// AVISO PARA A PRÓXIMA TELA
// ==========================================
// Guarda uma mensagem para ser exibida depois de um redirecionamento (ex.: "Condomínio cadastrado").
const CHAVE_AVISO = "zelus.aviso";

export function avisarNaProximaTela(mensagem, tipo = "success") {
    sessionStorage.setItem(CHAVE_AVISO, JSON.stringify({ mensagem, tipo }));
}

// Exibe (uma única vez) o aviso guardado pela tela anterior, se houver.
export function mostrarAvisoPendente(container) {
    const json = sessionStorage.getItem(CHAVE_AVISO);
    if (!json) return;
    sessionStorage.removeItem(CHAVE_AVISO);
    const { mensagem, tipo } = JSON.parse(json);
    mostrarAlerta(container, mensagem, tipo);
}