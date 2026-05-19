import { createNumpadFlow } from "/static/js/components/transaction-flow.js";

document.addEventListener("DOMContentLoaded", () => {
    createNumpadFlow({
        subtitles: {
            amount: "Qual é o valor do saque?",
            confirm: "Confirme o valor do saque",
            success: "Comprovante da operação",
        },
        formId: "saque-form",
    }).init();
});
