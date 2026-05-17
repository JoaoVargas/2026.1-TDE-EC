const state = {
    step: "amount",
    amountDigits: "",
    accountType: localStorage.getItem('conta_selecionada') || 'corrente', // lê direto do localStorage
};

function formatAmount(digits) {
    const cents = Number(digits || "0");
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function getAccountLabel() {
    return state.accountType === "poupanca" ? "Conta Poupança" : "Conta Corrente";
}

function updateAccountDisplay() {
    const balanceData = document.getElementById("balance-data");
    const balanceDisplay = document.getElementById("balance-display");
    const hiddenAccountType = document.getElementById("hidden-account-type");

    if (balanceData && balanceDisplay) {
        balanceDisplay.textContent = balanceData.dataset[state.accountType];
    }
    if (hiddenAccountType) {
        hiddenAccountType.value = state.accountType;
    }
}

function setStep(step) {
    state.step = step;
    const flow = document.querySelector(".transfer-flow");
    if (flow) flow.dataset.step = step;

    const subtitle = document.getElementById("transfer-subtitle");
    if (subtitle) {
        subtitle.textContent =
            step === "amount"   ? "Qual é o valor do depósito?"
            : step === "confirm"  ? "Confirme o valor do depósito"
            : "Comprovante da operação";
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

function populateConfirmStep() {
    updateAmountDisplay();
    const confirmAccountLabel = document.getElementById("confirm-account-label");
    if (confirmAccountLabel) {
        confirmAccountLabel.textContent = `Destino: ${getAccountLabel()}`;
    }
}

function writeReceipt() {
    const receiptAmount = document.getElementById("receipt-amount");
    const receiptDate = document.getElementById("receipt-date");
    const receiptAccount = document.getElementById("receipt-account");
    if (receiptAmount) receiptAmount.textContent = formatAmount(state.amountDigits);
    if (receiptDate) receiptDate.textContent = new Date().toLocaleString("pt-BR");
    if (receiptAccount) receiptAccount.textContent = getAccountLabel();
}

function submitDeposito() {
    const form = document.getElementById("deposito-form");
    const hiddenAmount = document.getElementById("hidden-amount");
    const hiddenAccountType = document.getElementById("hidden-account-type");
    if (!form || !hiddenAmount) return;
    hiddenAmount.value = state.amountDigits || "0";
    if (hiddenAccountType) hiddenAccountType.value = state.accountType;
    form.submit();
}

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();
    updateAccountDisplay(); // aplica saldo e hidden-account-type baseado no localStorage

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
        populateConfirmStep();
        setStep("confirm");
    });

    document.getElementById("btn-back-amount")?.addEventListener("click", () => {
        setStep("amount");
    });

    document.getElementById("btn-confirmar")?.addEventListener("click", () => {
        writeReceipt();
        setStep("success");
        submitDeposito();
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