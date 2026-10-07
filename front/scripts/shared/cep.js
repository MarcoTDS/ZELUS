// Consulta de endereço pelo CEP na API pública do ViaCEP (https://viacep.com.br).
import { VIACEP_URL } from "./config.js";

/**
 * Busca o endereço de um CEP.
 * Devolve { cep, rua, bairro, cidade, estado } ou null quando o CEP não existe.
 * Lança Error quando o ViaCEP não responde (sem internet, serviço fora do ar).
 *
 * @param {string} cep  Com ou sem máscara (ex.: "85851-000" ou "85851000")
 */
export async function buscarEnderecoPorCep(cep) {
    const digitos = cep.replace(/\D/g, "");
    if (digitos.length !== 8) return null;

    let resposta;
    try {
        resposta = await fetch(`${VIACEP_URL}/${digitos}/json/`);
    } catch {
        throw new Error("Não foi possível consultar o CEP. Preencha o endereço manualmente.");
    }

    // 400: CEP em formato inválido
    if (resposta.status === 400) return null;
    if (!resposta.ok) throw new Error("Não foi possível consultar o CEP. Preencha o endereço manualmente.");

    const dados = await resposta.json();

    // CEP com formato válido, mas inexistente: o ViaCEP responde { "erro": true }
    if (dados.erro) return null;

    return {
        cep: dados.cep,
        rua: dados.logradouro,   // CEPs de cidade pequena (CEP geral) vêm sem rua e bairro
        bairro: dados.bairro,
        cidade: dados.localidade,
        estado: dados.uf
    };
}
