const state = {
    step: "amount",
    amountDigits: "",
    selectedAccountId: null,
    selectedName: null,
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
            step === "amount" ? "Qual e o valor da transferencia?"
            : step === "recipient" ? "Para quem voce quer transferir?"
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
    if (display) display.textContent = value;
    if (selectedAmount) selectedAmount.textContent = value;
}

function filterRecipients(filterText) {
    const cards = document.querySelectorAll(".recipient-card");
    const normalized = filterText.trim().toLowerCase();
    cards.forEach((card) => {
        const name = (card.dataset.name || "").toLowerCase();
        const number = card.querySelector(".recipient-bank")?.textContent.toLowerCase() || "";
        const visible = !normalized || name.includes(normalized) || number.includes(normalized);
        card.style.display = visible ? "" : "none";
    });
}

function selectRecipient(card) {
    document.querySelectorAll(".recipient-card").forEach((c) => c.classList.remove("is-selected"));
    card.classList.add("is-selected");
    state.selectedAccountId = card.dataset.accountId;
    state.selectedName = card.dataset.name;
    const transferBtn = document.getElementById("btn-to-success");
    if (transferBtn) transferBtn.disabled = false;
}

function writeReceipt() {
    const amountText = formatAmount(state.amountDigits);
    const dateText = new Date().toLocaleString("pt-BR");

    const receiptAmount = document.getElementById("receipt-amount");
    const receiptName = document.getElementById("receipt-name");
    const receiptDate = document.getElementById("receipt-date");

    if (receiptAmount) receiptAmount.textContent = amountText;
    if (receiptName) receiptName.textContent = state.selectedName || "-";
    if (receiptDate) receiptDate.textContent = dateText;
}

function submitTransfer() {
    const form = document.getElementById("transfer-form");
    const hiddenAmount = document.getElementById("hidden-amount");
    const hiddenAccount = document.getElementById("hidden-to-account");

    if (!form || !hiddenAmount || !hiddenAccount) return;
    hiddenAmount.value = state.amountDigits || "0";
    hiddenAccount.value = state.selectedAccountId || "";
    form.submit();
}

function wireAmountStep() {
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

    document.getElementById("btn-to-recipient")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) return;
        setStep("recipient");
    });
}

function wireRecipientStep() {
    document.getElementById("btn-back-amount")?.addEventListener("click", () => {
        setStep("amount");
    });

    document.getElementById("recipient-search")?.addEventListener("input", (event) => {
        filterRecipients(event.target.value);
    });

    document.querySelectorAll(".recipient-card").forEach((card) => {
        card.addEventListener("click", () => selectRecipient(card));
    });

    document.getElementById("btn-to-success")?.addEventListener("click", () => {
        if (!state.selectedAccountId) return;
        writeReceipt();
        setStep("success");
    });
}

function wireSuccessStep() {
    document.getElementById("btn-finish-transfer")?.addEventListener("click", () => {
        submitTransfer();
    });
}

function wireCancelButton() {
    document.getElementById("btn-cancelar-transferencia")?.addEventListener("click", () => {
        if (state.step === "amount" || state.step === "success") {
            window.location.href = "/home";
            return;
        }
        if (state.step === "recipient") {
            setStep("amount");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();
    wireAmountStep();
    wireRecipientStep();
    wireSuccessStep();
    wireCancelButton();
});
