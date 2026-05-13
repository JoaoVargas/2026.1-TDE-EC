const state = {
    step: "amount",
    amountDigits: "",
};

function formatAmount(digits) {
    const cents = Number(digits || "0");
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function setStep(step) {
    state.step = step;
    const flow = document.querySelector(".transfer-flow");
    if (flow) flow.dataset.step = step;

    const subtitle = document.getElementById("transfer-subtitle");
    if (subtitle) {
        subtitle.textContent =
            step === "amount" ? "Qual e o valor do saque?"
            : step === "confirm" ? "Confirme o valor do saque"
            : "Comprovante da operacao";
    }

    document.querySelectorAll("[data-step-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.stepPanel === step);
    });
}

function updateAmountDisplay() {
    const value = formatAmount(state.amountDigits);
    const display = document.getElementById("amount-display");
    const selectedAmount = document.getElementById("selected-amount");
    const confirmAmount = document.getElementById("confirm-amount");
    if (display) display.textContent = value;
    if (selectedAmount) selectedAmount.textContent = value;
    if (confirmAmount) confirmAmount.textContent = value;
}

function submitSaque() {
    const form = document.getElementById("saque-form");
    const hiddenAmount = document.getElementById("hidden-amount");
    if (!form || !hiddenAmount) return;
    hiddenAmount.value = state.amountDigits || "0";
    form.submit();
}

function writeReceipt() {
    const receiptAmount = document.getElementById("receipt-amount");
    const receiptDate = document.getElementById("receipt-date");
    if (receiptAmount) receiptAmount.textContent = formatAmount(state.amountDigits);
    if (receiptDate) receiptDate.textContent = new Date().toLocaleString("pt-BR");
}

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();

    document.querySelectorAll(".numpad-key[data-number]").forEach((button) => {
        button.addEventListener("click", () => {
            if (state.amountDigits.length >= 9) return;
            state.amountDigits += button.dataset.number;
            updateAmountDisplay();
        });
    });

    document.getElementById("btn-delete")?.addEventListener("click", () => {
        state.amountDigits = state.amountDigits.slice(0, -1);
        updateAmountDisplay();
    });

    document.getElementById("btn-to-confirm")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) return;
        updateAmountDisplay();
        setStep("confirm");
    });

    document.getElementById("btn-back-amount")?.addEventListener("click", () => {
        setStep("amount");
    });

    document.getElementById("btn-confirmar")?.addEventListener("click", () => {
        writeReceipt();
        setStep("success");
        submitSaque();
    });

    document.getElementById("btn-finish")?.addEventListener("click", () => {
        window.location.href = "/home";
    });

    document.getElementById("btn-cancelar")?.addEventListener("click", () => {
        if (state.step === "confirm") {
            setStep("amount");
        } else {
            window.location.href = "/home";
        }
    });
});
