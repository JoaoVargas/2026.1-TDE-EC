const recipients = [
    { name: "Ana Silva", bank: "BetaBank", key: "ana.silva@bank.com" },
    { name: "Lucas Costa", bank: "Nubank", key: "lucas.costa@bank.com" },
    { name: "Maria Lima", bank: "Itau", key: "maria.lima@bank.com" },
    { name: "Bruno Souza", bank: "Santander", key: "bruno.souza@bank.com" },
    { name: "Clara Rocha", bank: "Inter", key: "clara.rocha@bank.com" },
    { name: "Ricardo Melo", bank: "C6", key: "ricardo.melo@bank.com" },
];

const state = {
    step: "amount",
    amountDigits: "",
    selectedRecipient: null,
};

function formatAmount(digits) {
    const cents = Number(digits || "0");
    return (cents / 100).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function setStep(step) {
    state.step = step;
    const flow = document.querySelector(".transfer-flow");
    if (flow) {
        flow.dataset.step = step;
    }

    const subtitle = document.getElementById("transfer-subtitle");
    if (subtitle) {
        subtitle.textContent =
            step === "amount"
                ? "Qual e o valor da transferencia?"
                : step === "recipient"
                ? "Para quem voce quer transferir?"
                : "Comprovante da operacao";
    }

    document.querySelectorAll("[data-step-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.stepPanel === step);
    });
}

function updateAmountDisplay() {
    const display = document.getElementById("amount-display");
    const selectedAmount = document.getElementById("selected-amount");
    const value = formatAmount(state.amountDigits);

    if (display) {
        display.textContent = value;
    }
    if (selectedAmount) {
        selectedAmount.textContent = value;
    }
}

function renderRecipients(filterText = "") {
    const grid = document.getElementById("recipient-grid");
    if (!grid) {
        return;
    }

    grid.innerHTML = "";
    const normalizedFilter = filterText.trim().toLowerCase();

    const filtered = recipients.filter((item) => {
        if (!normalizedFilter) {
            return true;
        }

        return (
            item.name.toLowerCase().includes(normalizedFilter) ||
            item.bank.toLowerCase().includes(normalizedFilter) ||
            item.key.toLowerCase().includes(normalizedFilter)
        );
    });

    filtered.forEach((recipient) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "recipient-card";
        card.innerHTML = `
            <span class="recipient-initial">${recipient.name.split(" ").map((p) => p[0]).slice(0, 2).join("")}</span>
            <span class="recipient-name">${recipient.name}</span>
            <span class="recipient-bank">${recipient.bank}</span>
        `;

        if (state.selectedRecipient?.key === recipient.key) {
            card.classList.add("is-selected");
        }

        card.addEventListener("click", () => {
            state.selectedRecipient = recipient;
            document.querySelectorAll(".recipient-card").forEach((node) => node.classList.remove("is-selected"));
            card.classList.add("is-selected");
            const transferBtn = document.getElementById("btn-to-success");
            if (transferBtn) {
                transferBtn.disabled = false;
            }
        });

        grid.appendChild(card);
    });
}

function writeReceipt() {
    const amountText = formatAmount(state.amountDigits);
    const target = state.selectedRecipient;
    const dateText = new Date().toLocaleString("pt-BR");

    const receiptAmount = document.getElementById("receipt-amount");
    const receiptName = document.getElementById("receipt-name");
    const receiptBank = document.getElementById("receipt-bank");
    const receiptDate = document.getElementById("receipt-date");

    if (receiptAmount) {
        receiptAmount.textContent = amountText;
    }
    if (receiptName) {
        receiptName.textContent = target?.name || "-";
    }
    if (receiptBank) {
        receiptBank.textContent = target?.bank || "-";
    }
    if (receiptDate) {
        receiptDate.textContent = dateText;
    }
}

function wireAmountStep() {
    document.querySelectorAll(".numpad-key[data-number]").forEach((button) => {
        button.addEventListener("click", () => {
            if (state.amountDigits.length >= 9) {
                return;
            }
            state.amountDigits += button.dataset.number;
            updateAmountDisplay();
        });
    });

    document.getElementById("btn-delete")?.addEventListener("click", () => {
        state.amountDigits = state.amountDigits.slice(0, -1);
        updateAmountDisplay();
    });

    document.getElementById("btn-to-recipient")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) {
            return;
        }
        setStep("recipient");
    });
}

function wireRecipientStep() {
    document.getElementById("btn-back-amount")?.addEventListener("click", () => {
        setStep("amount");
    });

    document.getElementById("recipient-search")?.addEventListener("input", (event) => {
        renderRecipients(event.target.value);
    });

    document.getElementById("btn-to-success")?.addEventListener("click", () => {
        if (!state.selectedRecipient) {
            return;
        }
        writeReceipt();
        setStep("success");
    });
}

function wireSuccessStep() {
    document.getElementById("btn-finish-transfer")?.addEventListener("click", () => {
        window.location.href = "/home";
    });
}

function wireCancelButton() {
    document.getElementById("btn-cancelar-transferencia")?.addEventListener("click", () => {
        if (state.step === "amount") {
            window.location.href = "/home";
            return;
        }

        if (state.step === "recipient") {
            setStep("amount");
            return;
        }

        if (state.step === "success") {
            window.location.href = "/home";
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();
    renderRecipients();
    wireAmountStep();
    wireRecipientStep();
    wireSuccessStep();
    wireCancelButton();
});
