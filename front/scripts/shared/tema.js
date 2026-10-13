// Alternância entre tema claro e escuro (Bootstrap: data-bs-theme no <html>).
//
// Como usar: carregar SEM defer e SEM type="module", dentro do <head>,
// para o tema ser aplicado antes da página aparecer (evita "piscar" de branco):
//   <script src="../../scripts/shared/tema.js"></script>
//
// O botão (#btnTema) pode existir no HTML (login) ou ser criado depois pelo
// layout.js (telas logadas); por isso o clique é escutado no document e um
// MutationObserver sincroniza o ícone assim que o botão aparece.
(function () {
    const CHAVE = "zelus-tema";

    function temaSalvo() {
        try {
            return localStorage.getItem(CHAVE) === "dark" ? "dark" : "light";
        } catch (erro) {
            return "light";
        }
    }

    function salvarTema(tema) {
        try {
            localStorage.setItem(CHAVE, tema);
        } catch (erro) {
            // Sem localStorage: o tema vale só até recarregar a página.
        }
    }

    function atualizarBotao() {
        const botao = document.getElementById("btnTema");
        if (!botao) return;

        const escuro = document.documentElement.getAttribute("data-bs-theme") === "dark";
        const lua = botao.querySelector(".icone-lua");
        const sol = botao.querySelector(".icone-sol");

        // Escuro mostra o sol (voltar ao claro); claro mostra a lua.
        if (lua) lua.classList.toggle("d-none", escuro);
        if (sol) sol.classList.toggle("d-none", !escuro);

        botao.setAttribute("aria-label", escuro ? "Mudar para modo claro" : "Mudar para modo escuro");
    }

    function aplicarTema(tema) {
        document.documentElement.setAttribute("data-bs-theme", tema);
        atualizarBotao();
    }

    // Aplica já, enquanto o <head> está sendo lido.
    aplicarTema(temaSalvo());

    // Delegação: funciona mesmo que o botão seja criado depois.
    document.addEventListener("click", function (evento) {
        if (!evento.target.closest("#btnTema")) return;

        const novo = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        salvarTema(novo);
        aplicarTema(novo);
    });

    // Quando o layout.js inserir o botão, acerta o ícone.
    document.addEventListener("DOMContentLoaded", function () {
        atualizarBotao();
        new MutationObserver(atualizarBotao).observe(document.body, { childList: true, subtree: true });
    });
})();