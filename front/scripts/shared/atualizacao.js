// Atualização automática das telas, sem recarregar a página.
// A consulta à API se repete a cada intervalo enquanto a aba está visível, e roda na hora
// quando o usuário volta para a aba. Não é tempo real (fora do escopo): a tela fica no máximo
// um intervalo atrasada em relação ao banco.
//
// Uso: atualizarPeriodicamente(() => carregarChamados({ silencioso: true }));
export const INTERVALO_ATUALIZACAO = 10000; // 10 segundos

export function atualizarPeriodicamente(atualizar, intervalo = INTERVALO_ATUALIZACAO) {
    let emAndamento = false;

    async function executar() {
        if (document.hidden || emAndamento) return;
        emAndamento = true;
        try {
            await atualizar();
        } catch (erro) {
            // Falha numa atualização em segundo plano não interrompe a tela; tenta de novo no próximo ciclo
            console.warn("Atualização automática falhou:", erro);
        } finally {
            emAndamento = false;
        }
    }

    setInterval(executar, intervalo);
    document.addEventListener("visibilitychange", executar);
}
