import { formatCpf, onlyDigits } from "/static/js/components/formatters.js";

document.addEventListener("DOMContentLoaded", () => {
    const cpfField = document.getElementById("cpf");
    if (!cpfField) {
        return;
    }

    cpfField.addEventListener("input", (event) => {
        const value = event.target.value;
        if (!value.includes("@")) {
            event.target.value = formatCpf(value);
        }
    });

    const form = document.getElementById("form-login");
    if (form) {
        form.addEventListener("submit", (event) => {
            const cpfValue = cpfField.value;
            if (!cpfValue.includes("@")) {
                cpfField.value = onlyDigits(cpfValue);
            }
        });
    }
});
