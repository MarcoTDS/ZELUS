// Exibe o resultado do cadastro do síndico / reenvio do link (RN12, RN13).
// A API envia por e-mail o link de validação e a senha provisória, e também devolve esses dados
// no response: se o e-mail falhar (email_enviado = false), o administrador pode repassá-los.
import { escaparHtml } from "../shared/ui.js";

export function mostrarAcessoSindico(container, acesso) {
    const enviado = acesso.email_enviado;
    const titulo = enviado
        ? `E-mail enviado para ${escaparHtml(acesso.email)}`
        : `Não foi possível enviar o e-mail para ${escaparHtml(acesso.email)}`;
    const orientacao = enviado
        ? "O síndico recebeu o link de validação e a senha provisória. Os dados abaixo ficam aqui caso ele precise."
        : "Repasse os dados abaixo ao síndico ou tente reenviar. Verifique a configuração de SMTP no .env da API.";

    container.innerHTML = `
        <div class="alert ${enviado ? "alert-success" : "alert-warning"} mt-3" role="status">
            <p class="fw-semibold mb-2" id="status-email">${titulo}</p>
            <p class="small mb-2">${orientacao}</p>
            <dl class="row small mb-0">
                <dt class="col-sm-4">E-mail (login)</dt>
                <dd class="col-sm-8">${escaparHtml(acesso.email)}</dd>
                <dt class="col-sm-4">Senha provisória</dt>
                <dd class="col-sm-8"><code id="senha-provisoria">${escaparHtml(acesso.senha_provisoria)}</code></dd>
                <dt class="col-sm-4">Link de validação</dt>
                <dd class="col-sm-8 text-break mb-0">
                    <a href="${escaparHtml(acesso.link_validacao)}" target="_blank" id="link-validacao">${escaparHtml(acesso.link_validacao)}</a>
                </dd>
            </dl>
        </div>
    `;
}
