// Detalhes visuais da tela de primeiro acesso: requisitos da senha (ficam verdes)
// e botão "Mostrar senhas". Envio, confirmação e redirecionamento ficam no trocar-senha.js.
const provisoria = document.getElementById("senhaProvisoria");
const nova = document.getElementById("novaSenha");
const confirmar = document.getElementById("confirmarSenha");
const erroNova = document.getElementById("erroNovaSenha");

function regras() {
    return {
        tamanho: nova.value.length >= 8,
        diferente: nova.value.length > 0 && nova.value !== provisoria.value
    };
}

function validarNovaSenha() {
    const r = regras();

    document.querySelectorAll("#requisitos li").forEach((li) => {
        li.classList.toggle("ok", r[li.dataset.regra]);
    });

    if (!r.tamanho) {
        nova.setCustomValidity("curta");
        erroNova.textContent = "A senha precisa ter pelo menos 8 caracteres.";
    } else if (!r.diferente) {
        nova.setCustomValidity("igual");
        erroNova.textContent = "A nova senha precisa ser diferente da provisória.";
    } else {
        nova.setCustomValidity("");
    }
}

provisoria.addEventListener("input", validarNovaSenha);
nova.addEventListener("input", validarNovaSenha);
// Garante a validação também no envio (antes do checkValidity do trocar-senha.js)
document.getElementById("form-senha").addEventListener("submit", validarNovaSenha, true);

const botaoMostrar = document.getElementById("mostrarSenhas");
botaoMostrar.addEventListener("click", () => {
    const mostrar = provisoria.type === "password";
    [provisoria, nova, confirmar].forEach((campo) => { campo.type = mostrar ? "text" : "password"; });
    botaoMostrar.textContent = mostrar ? "Ocultar senhas" : "Mostrar senhas";
});