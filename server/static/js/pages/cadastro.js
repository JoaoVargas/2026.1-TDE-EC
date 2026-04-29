import { redirectIfAuthenticated } from "/static/js/components/auth-token-guard.js";
import { showFieldError, showGlobalMessage } from "/static/js/components/form-feedback.js";
import { formatCep, formatCpf, onlyDigits } from "/static/js/components/formatters.js";

const API_URL = "/api/cadastro";
const VERIFY_URL = "/api/verificar";

const rules = {
    nome: (v) => {
        if (!v) {
            return "Nome completo e obrigatorio.";
        }
        if (v.length < 3) {
            return "Nome deve ter pelo menos 3 caracteres.";
        }
        return /^[A-Za-zÀ-ſ\s]+$/.test(v) ? null : "Nome nao pode conter numeros ou simbolos.";
    },
    email: (v) => {
        if (!v) {
            return "E-mail e obrigatorio.";
        }
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : "Informe um e-mail valido.";
    },
    cpf: (v) => {
        const digits = onlyDigits(v);
        if (!digits) {
            return "CPF e obrigatorio.";
        }
        if (digits.length !== 11) {
            return "CPF deve ter 11 digitos.";
        }
        return validarCPF(digits) ? null : "CPF invalido.";
    },
    nascimento: (v) => {
        if (!v) {
            return "Data de nascimento e obrigatoria.";
        }

        const nascimento = new Date(v);
        const hoje = new Date();
        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const monthDiff = hoje.getMonth() - nascimento.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && hoje.getDate() < nascimento.getDate())) {
            idade -= 1;
        }

        if (idade < 18) {
            return "Voce deve ter pelo menos 18 anos.";
        }
        return idade > 120 ? "Data de nascimento invalida." : null;
    },
    senha: (v) => {
        if (!v) {
            return "Senha e obrigatoria.";
        }
        if (v.length < 8) {
            return "Senha deve ter pelo menos 8 caracteres.";
        }
        if (!/[A-Z]/.test(v)) {
            return "Senha deve conter pelo menos uma letra maiuscula.";
        }
        return /[0-9]/.test(v) ? null : "Senha deve conter pelo menos um numero.";
    },
    confirmar: (v) => {
        const senha = document.getElementById("senha")?.value || "";
        if (!v) {
            return "Confirmacao de senha e obrigatoria.";
        }
        return v === senha ? null : "As senhas nao coincidem.";
    },
    cep: (v) => {
        const digits = onlyDigits(v);
        if (!digits) {
            return "CEP e obrigatorio.";
        }
        return digits.length === 8 ? null : "CEP deve ter 8 digitos.";
    },
    logradouro: (v) => (v ? null : "Logradouro e obrigatorio."),
    numero: (v) => (v ? null : "Numero e obrigatorio."),
    bairro: (v) => (v ? null : "Bairro e obrigatorio."),
    cidade: (v) => (v ? null : "Cidade e obrigatoria."),
    estado: (v) => {
        if (!v) {
            return "Estado e obrigatorio.";
        }
        return v.length === 2 ? null : "Use a sigla do estado (ex: PR).";
    },
};

function validarCPF(nums) {
    if (/^(\d)\1{10}$/.test(nums)) {
        return false;
    }

    let soma = 0;
    for (let i = 0; i < 9; i += 1) {
        soma += Number(nums[i]) * (10 - i);
    }
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) {
        resto = 0;
    }
    if (resto !== Number(nums[9])) {
        return false;
    }

    soma = 0;
    for (let i = 0; i < 10; i += 1) {
        soma += Number(nums[i]) * (11 - i);
    }
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) {
        resto = 0;
    }
    return resto === Number(nums[10]);
}

function validateField(fieldId) {
    const input = document.getElementById(fieldId);
    const validator = rules[fieldId];
    if (!input || !validator) {
        return true;
    }

    const error = validator(input.value.trim());
    showFieldError(input, error);
    return !error;
}

function wireRealtimeValidation() {
    Object.keys(rules).forEach((fieldId) => {
        const input = document.getElementById(fieldId);
        if (!input) {
            return;
        }

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

async function checkAvailability(param, value, fieldId, message) {
    try {
        const response = await fetch(`${VERIFY_URL}?${param}=${encodeURIComponent(value)}`);
        const result = await response.json();
        if (!result.disponivel) {
            const input = document.getElementById(fieldId);
            if (input) {
                showFieldError(input, message);
            }
        }
    } catch {
        // noop
    }
}

async function lookupCep() {
    const cep = onlyDigits(document.getElementById("cep")?.value || "");
    if (cep.length !== 8) {
        return;
    }

    try {
        const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
        const result = await response.json();
        if (result.erro) {
            return;
        }

        const map = {
            logradouro: result.logradouro || "",
            bairro: result.bairro || "",
            cidade: result.localidade || "",
            estado: result.uf || "",
        };

        Object.entries(map).forEach(([id, value]) => {
            const input = document.getElementById(id);
            if (!input) {
                return;
            }
            input.value = value;
            validateField(id);
        });
    } catch {
        // noop
    }
}

function buildPayload() {
    return {
        name: document.getElementById("nome").value.trim(),
        email: document.getElementById("email").value.trim(),
        cpf: onlyDigits(document.getElementById("cpf").value),
        birthday: document.getElementById("nascimento").value,
        password: document.getElementById("senha").value,
        address: {
            cep: onlyDigits(document.getElementById("cep").value),
            street: document.getElementById("logradouro").value.trim(),
            number: document.getElementById("numero").value.trim(),
            neighborhood: document.getElementById("bairro").value.trim(),
            city: document.getElementById("cidade").value.trim(),
            state: document.getElementById("estado").value.trim().toUpperCase(),
        },
    };
}

async function submitRegister() {
    const fields = Object.keys(rules);
    const valid = fields.map(validateField).every(Boolean);
    const messageEl = document.getElementById("mensagem");

    if (!valid) {
        showGlobalMessage(messageEl, "Corrija os erros antes de continuar.", "erro");
        return;
    }

    const submitBtn = document.getElementById("btn-finalizar");
    submitBtn.disabled = true;
    submitBtn.textContent = "Enviando...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(buildPayload()),
        });
        const result = await response.json();

        if (response.status === 409) {
            showGlobalMessage(messageEl, "CPF ou e-mail ja cadastrado.", "erro");
            return;
        }

        if (!response.ok) {
            showGlobalMessage(messageEl, result.detail || "Erro ao realizar cadastro.", "erro");
            return;
        }

        showGlobalMessage(messageEl, "Cadastro realizado com sucesso!", "sucesso");
        localStorage.removeItem("cadastro_rascunho");
        window.location.href = "/login";
    } catch {
        showGlobalMessage(messageEl, "Nao foi possivel conectar ao servidor.", "erro");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Finalizar cadastro";
    }
}

function hydrateDraft() {
    const draft = JSON.parse(localStorage.getItem("cadastro_rascunho") || "null");
    if (!draft) {
        return;
    }

    document.getElementById("nome").value = draft.name || "";
    document.getElementById("email").value = draft.email || "";
    document.getElementById("cpf").value = formatCpf(draft.cpf || "");
    document.getElementById("nascimento").value = draft.birthday || "";

    document.getElementById("cep").value = formatCep(draft.address?.cep || "");
    document.getElementById("logradouro").value = draft.address?.street || "";
    document.getElementById("numero").value = draft.address?.number || "";
    document.getElementById("bairro").value = draft.address?.neighborhood || "";
    document.getElementById("cidade").value = draft.address?.city || "";
    document.getElementById("estado").value = draft.address?.state || "";
}

function persistDraft() {
    const payload = buildPayload();
    delete payload.password;
    localStorage.setItem("cadastro_rascunho", JSON.stringify(payload));
}

document.addEventListener("DOMContentLoaded", async () => {
    await redirectIfAuthenticated();

    hydrateDraft();
    wireRealtimeValidation();

    document.getElementById("cpf")?.addEventListener("input", (event) => {
        event.target.value = formatCpf(event.target.value);
        persistDraft();
    });

    document.getElementById("cep")?.addEventListener("input", (event) => {
        event.target.value = formatCep(event.target.value);
        persistDraft();
    });

    document.getElementById("estado")?.addEventListener("input", (event) => {
        event.target.value = event.target.value.toUpperCase().slice(0, 2);
        persistDraft();
    });

    ["nome", "email", "nascimento", "logradouro", "numero", "bairro", "cidade", "senha", "confirmar"].forEach((fieldId) => {
        document.getElementById(fieldId)?.addEventListener("input", persistDraft);
    });

    document.getElementById("cep")?.addEventListener("blur", lookupCep);

    document.getElementById("cpf")?.addEventListener("blur", (event) => {
        const cpf = onlyDigits(event.target.value);
        if (cpf.length === 11 && validarCPF(cpf)) {
            checkAvailability("cpf", cpf, "cpf", "CPF ja cadastrado.");
        }
    });

    document.getElementById("email")?.addEventListener("blur", (event) => {
        const email = event.target.value.trim();
        if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            checkAvailability("email", email, "email", "E-mail ja cadastrado.");
        }
    });

    document.getElementById("btn-finalizar")?.addEventListener("click", submitRegister);
});
