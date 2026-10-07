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
