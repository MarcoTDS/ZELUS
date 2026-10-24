// Formatação de datas, prazos de SLA e status de chamados, usada pelas telas de chamados e cadastros.

// A API devolve datas em UTC sem fuso (ex.: "2026-10-07T14:32:00"); o "Z" faz o navegador converter para o horário local.
export function lerDataApi(texto) {
    if (!texto) return null;
    return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(texto) ? texto : `${texto}Z`);
}

// "22/08/2026 às 14:32"
export function formatarDataHora(texto) {
    const data = lerDataApi(texto);
    if (!data) return "";
    const dia = data.toLocaleDateString("pt-BR");
    const hora = data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    return `${dia} às ${hora}`;
}

// Número do ticket com 4 dígitos: 30 -> "#0030"
export function formatarTicket(id) {
    return `#${String(id).padStart(4, "0")}`;
}

// Duração em horas e minutos, sempre truncada (nunca arredonda para cima nem esconde minutos):
// "menos de 1 min", "35 min", "5h 59min", "8h", "1 dia", "1 dia e 3h 20min", "3 dias e 5 min"
export function formatarDuracao(milissegundos) {
    const totalMinutos = Math.floor(Math.abs(milissegundos) / 60000);
    if (totalMinutos < 1) return "menos de 1 min";

    const dias = Math.floor(totalMinutos / 1440);
    const horas = Math.floor((totalMinutos % 1440) / 60);
    const minutos = totalMinutos % 60;

    let resto = "";
    if (horas && minutos) resto = `${horas}h ${String(minutos).padStart(2, "0")}min`;
    else if (horas) resto = `${horas}h`;
    else if (minutos) resto = `${minutos} min`;

    if (dias === 0) return resto;
    const textoDias = `${dias} ${dias === 1 ? "dia" : "dias"}`;
    return resto ? `${textoDias} e ${resto}` : textoDias;
}

// Prazo de SLA de uma categoria (em horas): "24h", "72h (3 dias)"
export function formatarPrazoSla(horas) {
    const inteiro = Math.round(horas);
    return inteiro >= 48 && inteiro % 24 === 0 ? `${inteiro}h (${inteiro / 24} dias)` : `${inteiro}h`;
}

// RN04: "Expira em 5h 59min" ou "Vencido há 2h 10min" a partir da data de vencimento do SLA.
// Usado por todas as telas (fila do síndico e detalhes do chamado), para mostrarem o mesmo valor.
export function descreverPrazo(dataVencimento) {
    const restante = lerDataApi(dataVencimento) - new Date();
    return restante >= 0 ? `Expira em ${formatarDuracao(restante)}` : `Vencido há ${formatarDuracao(restante)}`;
}

// Selo do status do chamado. RN04: chamado vencido mostra "Vencido" no lugar do status.
const CLASSES_STATUS = {
    "Aberto": "status-aberto",
    "Em Andamento": "status-andamento",
    "Resolvido": "status-resolvido",
    "Cancelado": "status-cancelado"
};

export function seloStatus(chamado) {
    if (chamado.vencido) {
        return `<span class="badge selo-status status-vencido">Vencido</span>`;
    }
    return `<span class="badge selo-status ${CLASSES_STATUS[chamado.status] || "text-bg-secondary"}">${chamado.status}</span>`;
}
