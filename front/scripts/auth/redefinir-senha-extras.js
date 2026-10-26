// Detalhes visuais da tela de redefinir senha: requisito da senha (fica verde)
// e botão "Mostrar senhas". Envio, confirmação e token ficam no redefinir-senha.js.
const nova = document.getElementById("nova_senha");
const confirmar = document.getElementById("confirmar_nova_senha");
const requisito = document.querySelector("#requisitos li");

function atualizarRequisito() {
    requisito.classList.toggle("ok", nova.value.length >= 6);
}
nova.addEventListener("input", atualizarRequisito);

const botaoMostrar = document.getElementById("mostrarSenhas");
botaoMostrar.addEventListener("click", () => {
    const mostrar = nova.type === "password";
    [nova, confirmar].forEach((campo) => { campo.type = mostrar ? "text" : "password"; });
    botaoMostrar.textContent = mostrar ? "Ocultar senhas" : "Mostrar senhas";
});