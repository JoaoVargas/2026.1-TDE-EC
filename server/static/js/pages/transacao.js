import { formatAmount, getAccountLabel as getLabel, wireNumpadKeyboard } from "/static/js/components/transaction-flow.js";

const state = {
    step: "amount",
    amountDigits: "",
    selectedAccountId: null,
    selectedName: null,
    accountType: "corrente",
};

function getAccountLabel() {
    return getLabel(state.accountType);
}

function updateAccountDisplay() {
    const balanceData = document.getElementById("balance-data");
    const balanceDisplay = document.getElementById("balance-display");
    const hiddenAccountType = document.getElementById("hidden-from-account-type");

    if (balanceData && balanceDisplay) {
        balanceDisplay.textContent = balanceData.dataset[state.accountType];
    }
    if (hiddenAccountType) {
        hiddenAccountType.value = state.accountType;
    }
}

function clearInlineError() {
    const errorDiv = document.getElementById("inline-transfer-error");
    if (errorDiv) errorDiv.style.display = "none";
}

function setStep(step) {
    state.step = step;
    clearInlineError();

    const flow = document.querySelector(".transfer-flow");
    if (flow) flow.dataset.step = step;

    const subtitle = document.getElementById("transfer-subtitle");
    if (subtitle) {
        subtitle.textContent =
            step === "amount"    ? "Qual é o valor da transferência?"
            : step === "recipient" ? "Para quem você quer transferir?"
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
    if (display) display.textContent = value;
    if (selectedAmount) selectedAmount.textContent = value;
}

function appendDigit(digit) {
    if (state.amountDigits.length >= 9) return;
    state.amountDigits += digit;
    updateAmountDisplay();
}

function deleteDigit() {
    state.amountDigits = state.amountDigits.slice(0, -1);
    updateAmountDisplay();
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
    const receiptAmount = document.getElementById("receipt-amount");
    const receiptName = document.getElementById("receipt-name");
    const receiptDate = document.getElementById("receipt-date");
    const receiptAccount = document.getElementById("receipt-account");

    if (receiptAmount) receiptAmount.textContent = formatAmount(state.amountDigits);
    if (receiptName) receiptName.textContent = state.selectedName || "-";
    if (receiptDate) receiptDate.textContent = new Date().toLocaleString("pt-BR");
    if (receiptAccount) receiptAccount.textContent = getAccountLabel();
}

async function submitAndCheck() {
    const form = document.getElementById("transfer-form");
    const hiddenAmount = document.getElementById("hidden-amount");
    const hiddenAccount = document.getElementById("hidden-to-account");
    const hiddenAccountType = document.getElementById("hidden-from-account-type");

    if (!form || !hiddenAmount || !hiddenAccount) return;
    hiddenAmount.value = state.amountDigits || "0";
    hiddenAccount.value = state.selectedAccountId || "";
    if (hiddenAccountType) hiddenAccountType.value = state.accountType;

    const btn = document.getElementById("btn-to-success");
    if (btn) btn.disabled = true;

    const errorMap = {
        saldo_insuficiente: "Saldo insuficiente para esta transferência.",
        valor_invalido: "Valor de transferência inválido.",
        destinatario_invalido: "Destinatário não encontrado.",
        sem_conta: "Nenhuma conta encontrada para o usuário.",
    };

    try {
        const response = await fetch("/transacao", {
            method: "POST",
            body: new FormData(form),
        });

        const finalUrl = new URL(response.url);

        if (finalUrl.pathname === "/home") {
            writeReceipt();
            setStep("success");
        } else {
            const errorKey = finalUrl.searchParams.get("error");
            const msg = errorMap[errorKey] || "Erro ao realizar transferência.";
            let errorDiv = document.getElementById("inline-transfer-error");
            if (!errorDiv) {
                errorDiv = document.createElement("div");
                errorDiv.id = "inline-transfer-error";
                errorDiv.className = "feedback-message mensagem erro feedback-error";
                errorDiv.style.marginBottom = "1rem";
                form.parentElement.insertBefore(errorDiv, form.nextSibling);
            }
            errorDiv.textContent = msg;
            errorDiv.style.display = "block";
            setTimeout(() => { errorDiv.style.display = "none"; }, 3000);
        }
    } catch {
        alert("Erro de conexão. Tente novamente.");
    } finally {
        if (btn) btn.disabled = false;
    }
}

function setupOwnAccountButton() {
    const balanceData = document.getElementById("balance-data");
    const btn = document.getElementById("btn-own-account");
    const nameEl = document.getElementById("own-account-name");
    const initialEl = document.getElementById("own-account-initial");
    if (!btn || !balanceData) return;

    const targetType = state.accountType === "corrente" ? "poupanca" : "corrente";
    const targetId = targetType === "corrente"
        ? balanceData.dataset.correnteId
        : balanceData.dataset.poupancaId;
    const targetLabel = targetType === "corrente" ? "Conta Corrente" : "Conta Poupança";
    const targetInitial = targetType === "corrente" ? "CC" : "CP";

    btn.dataset.accountId = targetId;
    btn.dataset.name = targetLabel;
    if (nameEl) nameEl.textContent = targetLabel;
    if (initialEl) initialEl.textContent = targetInitial;
}

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();
    updateAccountDisplay();

    // source account tabs
    document.querySelectorAll(".transfer-account-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".transfer-account-tab").forEach((t) => t.classList.remove("is-active"));
            tab.classList.add("is-active");
            state.accountType = tab.dataset.account;
            updateAccountDisplay();
            setupOwnAccountButton();
        });
    });

    // numpad clicks
    document.querySelectorAll(".numpad-key[data-number]").forEach((button) => {
        button.addEventListener("click", () => appendDigit(button.dataset.number));
    });
    document.getElementById("btn-delete")?.addEventListener("click", deleteDigit);

    // amount step
    document.getElementById("btn-to-recipient")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) return;
        setStep("recipient");
    });

    // recipient step
    document.getElementById("btn-back-amount")?.addEventListener("click", () => setStep("amount"));
    setupOwnAccountButton();
    document.getElementById("btn-own-account")?.addEventListener("click", () => {
        selectRecipient(document.getElementById("btn-own-account"));
    });
    document.getElementById("recipient-search")?.addEventListener("input", (e) => {
        filterRecipients(e.target.value);
    });
    document.querySelectorAll(".recipient-card").forEach((card) => {
        card.addEventListener("click", () => selectRecipient(card));
    });
    document.getElementById("btn-to-success")?.addEventListener("click", () => {
        if (!state.selectedAccountId) return;
        submitAndCheck();
    });

    // success step
    document.getElementById("btn-finish-transfer")?.addEventListener("click", () => {
        window.location.href = "/home";
    });

    // cancel
    document.getElementById("btn-cancelar-transferencia")?.addEventListener("click", () => {
        if (state.step === "amount" || state.step === "success") {
            window.location.href = "/home";
        } else if (state.step === "recipient") {
            setStep("amount");
        }
    });

    // keyboard
    wireNumpadKeyboard({
        onDigit: appendDigit,
        onDelete: deleteDigit,
        onEnter: () => {
            if (state.step === "amount") {
                if (!state.amountDigits || Number(state.amountDigits) === 0) return;
                setStep("recipient");
            } else if (state.step === "recipient") {
                if (!state.selectedAccountId) return;
                submitAndCheck();
            } else if (state.step === "success") {
                window.location.href = "/home";
            }
        },
        onEscape: () => document.getElementById("btn-cancelar-transferencia")?.click(),
    });
});
