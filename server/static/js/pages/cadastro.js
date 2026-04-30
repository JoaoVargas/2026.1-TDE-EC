import { showFieldError } from "/static/js/components/form-feedback.js";
import { formatCep, formatCpf, onlyDigits } from "/static/js/components/formatters.js";

const rules = {
    nome: (v) => {
        if (!v) return "Nome completo e obrigatorio.";
        if (v.length < 3) return "Nome deve ter pelo menos 3 caracteres.";
        return /^[A-Za-zÀ-ſ\s]+$/.test(v) ? null : "Nome nao pode conter numeros ou simbolos.";
    },
    email: (v) => {
        if (!v) return "E-mail e obrigatorio.";
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : "Informe um e-mail valido.";
    },
    cpf: (v) => {
        const digits = onlyDigits(v);
        if (!digits) return "CPF e obrigatorio.";
        if (digits.length !== 11) return "CPF deve ter 11 digitos.";
        return validarCPF(digits) ? null : "CPF invalido.";
    },
    nascimento: (v) => {
        if (!v) return "Data de nascimento e obrigatoria.";
        const nascimento = new Date(v);
        const hoje = new Date();
        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const monthDiff = hoje.getMonth() - nascimento.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && hoje.getDate() < nascimento.getDate())) {
            idade -= 1;
        }
        if (idade < 18) return "Voce deve ter pelo menos 18 anos.";
        return idade > 120 ? "Data de nascimento invalida." : null;
    },
    senha: (v) => {
        if (!v) return "Senha e obrigatoria.";
        if (v.length < 8) return "Senha deve ter pelo menos 8 caracteres.";
        if (!/[A-Z]/.test(v)) return "Senha deve conter pelo menos uma letra maiuscula.";
        return /[0-9]/.test(v) ? null : "Senha deve conter pelo menos um numero.";
    },
    confirmar: (v) => {
        const senha = document.getElementById("senha")?.value || "";
        if (!v) return "Confirmacao de senha e obrigatoria.";
        return v === senha ? null : "As senhas nao coincidem.";
    },
    cep: (v) => {
        const digits = onlyDigits(v);
        if (!digits) return "CEP e obrigatorio.";
        return digits.length === 8 ? null : "CEP deve ter 8 digitos.";
    },
    logradouro: (v) => (v ? null : "Logradouro e obrigatorio."),
    numero: (v) => (v ? null : "Numero e obrigatorio."),
    bairro: (v) => (v ? null : "Bairro e obrigatorio."),
    cidade: (v) => (v ? null : "Cidade e obrigatoria."),
    estado: (v) => {
        if (!v) return "Estado e obrigatorio.";
        return v.length === 2 ? null : "Use a sigla do estado (ex: PR).";
    },
};

function validarCPF(nums) {
    if (/^(\d)\1{10}$/.test(nums)) return false;
    let soma = 0;
    for (let i = 0; i < 9; i += 1) soma += Number(nums[i]) * (10 - i);
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== Number(nums[9])) return false;
    soma = 0;
    for (let i = 0; i < 10; i += 1) soma += Number(nums[i]) * (11 - i);
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    return resto === Number(nums[10]);
}

function validateField(fieldId) {
    const input = document.getElementById(fieldId);
    const validator = rules[fieldId];
    if (!input || !validator) return true;
    const error = validator(input.value.trim());
    showFieldError(input, error);
    return !error;
}

function wireRealtimeValidation() {
    Object.keys(rules).forEach((fieldId) => {
        const input = document.getElementById(fieldId);
        if (!input) return;
        input.addEventListener("blur", () => validateField(fieldId));
        input.addEventListener("input", () => {
            if (input.classList.contains("input-erro") || input.classList.contains("input-ok")) {
                validateField(fieldId);
            }
        });
        if (fieldId === "senha") {
            input.addEventListener("input", () => validateField("confirmar"));
        }
    });
}

async function lookupCep() {
    const cep = onlyDigits(document.getElementById("cep")?.value || "");
    if (cep.length !== 8) return;
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const result = await response.json();
        if (result.erro) return;
        const map = {
            logradouro: result.logradouro || "",
            bairro: result.bairro || "",
            cidade: result.localidade || "",
            estado: result.uf || "",
        };
        Object.entries(map).forEach(([id, value]) => {
            const input = document.getElementById(id);
            if (!input) return;
            input.value = value;
            validateField(id);
        });
    } catch {
        // noop
    }
}

document.addEventListener("DOMContentLoaded", () => {
    wireRealtimeValidation();

    document.getElementById("cpf")?.addEventListener("input", (event) => {
        event.target.value = formatCpf(event.target.value);
    });

    document.getElementById("cep")?.addEventListener("input", (event) => {
        event.target.value = formatCep(event.target.value);
    });

    document.getElementById("estado")?.addEventListener("input", (event) => {
        event.target.value = event.target.value.toUpperCase().slice(0, 2);
    });

    document.getElementById("cep")?.addEventListener("blur", lookupCep);

    const form = document.getElementById("form-cadastro");
    if (form) {
        form.addEventListener("submit", (event) => {
            const fields = Object.keys(rules);
            const valid = fields.map(validateField).every(Boolean);
            if (!valid) {
                event.preventDefault();
            } else {
                const cpfInput = document.getElementById("cpf");
                if (cpfInput) cpfInput.value = onlyDigits(cpfInput.value);
                const cepInput = document.getElementById("cep");
                if (cepInput) cepInput.value = onlyDigits(cepInput.value);
            }
        });
    }
});
