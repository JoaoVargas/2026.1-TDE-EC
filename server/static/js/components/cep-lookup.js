import { onlyDigits } from "./formatters.js";

export function wireCepLookup({ cepInput, streetInput, neighborhoodInput, cityInput, stateInput, numberInput }) {
    async function lookup() {
        const cep = onlyDigits(cepInput.value);
        if (cep.length !== 8) return;
        try {
            const res = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            const data = await res.json();
            if (data.erro) return;
            streetInput.value       = data.logradouro || "";
            neighborhoodInput.value = data.bairro      || "";
            cityInput.value         = data.localidade  || "";
            stateInput.value        = data.uf          || "";
            if (numberInput) numberInput.value = "";
        } catch {
            // noop
        }
    }

    cepInput.addEventListener("blur", lookup);
}
