import { createNumpadFlow } from "/static/js/components/transaction-flow.js";

document.addEventListener("DOMContentLoaded", () => {
    createNumpadFlow({
        subtitles: {
            amount: "Qual é o valor do depósito?",
            confirm: "Confirme o valor do depósito",
            success: "Comprovante da operação",
        },
        formId: "deposito-form",
    }).init();
});
