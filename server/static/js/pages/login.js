import {
    getDefaultRouteForUser,
    redirectIfAuthenticated,
} from "/static/js/components/auth-token-guard.js";
import { showFieldError, showGlobalMessage } from "/static/js/components/form-feedback.js";
import { formatCpf, onlyDigits } from "/static/js/components/formatters.js";

const API_URL = "/api/login";

const rules = {
    cpf: (value) => {
        if (!value) {
            return "CPF ou e-mail e obrigatorio.";
        }

        if (value.includes("@")) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
                ? null
                : "Informe um e-mail valido.";
        }

        return onlyDigits(value).length === 11 ? null : "CPF deve ter 11 digitos.";
    },
    senha: (value) => {
        if (!value) {
            return "Senha e obrigatoria.";
        }
        return value.length >= 8 ? null : "Senha deve ter pelo menos 8 caracteres.";
    },
};

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
    });
}

async function submitLogin() {
    const valid = Object.keys(rules).map(validateField).every(Boolean);
    if (!valid) {
        return;
    }

    const cpfField = document.getElementById("cpf");
    const senhaField = document.getElementById("senha");
    const messageEl = document.getElementById("mensagem");
    const submitBtn = document.getElementById("btn-login");

    const loginValue = cpfField.value.includes("@") ? cpfField.value.trim() : onlyDigits(cpfField.value);
    const payload = {
        cpf: loginValue,
        password: senhaField.value,
    };

    submitBtn.disabled = true;
    submitBtn.textContent = "Entrando...";

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await response.json();

        if (!response.ok) {
            showGlobalMessage(messageEl, result.detail || "CPF/e-mail ou senha incorretos.", "erro");
            return;
        }

        localStorage.setItem("token", result.token);
        localStorage.setItem("user", JSON.stringify(result.user));
        showGlobalMessage(messageEl, "Login realizado com sucesso!", "sucesso");
        window.location.href = getDefaultRouteForUser(result.user);
    } catch {
        showGlobalMessage(messageEl, "Nao foi possivel conectar ao servidor.", "erro");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Entrar";
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await redirectIfAuthenticated();

    const cpfField = document.getElementById("cpf");
    if (cpfField) {
        cpfField.addEventListener("input", (event) => {
            const value = event.target.value;
            if (!value.includes("@")) {
                event.target.value = formatCpf(value);
            }
        });
    }

    wireRealtimeValidation();
    document.getElementById("btn-login")?.addEventListener("click", submitLogin);
});
