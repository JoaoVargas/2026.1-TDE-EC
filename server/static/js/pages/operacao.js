import { formatAmount, getAccountLabel, wireNumpadKeyboard } from "/static/js/components/transaction-flow.js";

const flow = document.querySelector(".transfer-flow");
const MODE = flow?.dataset.mode ?? "depositar";

const state = {
    step: "amount",
    amountDigits: "",
    accountType: "corrente",   // only matters for transferir
    selectedAccountId: null,
    selectedName: null,
};

const SUBTITLES = {
    depositar:  { amount: "Qual é o valor do depósito?",      confirm:   "Confirme o valor do depósito",    success: "Comprovante da operação" },
    sacar:      { amount: "Qual é o valor do saque?",          confirm:   "Confirme o valor do saque",       success: "Comprovante da operação" },
    transferir: { amount: "Qual é o valor da transferência?",  recipient: "Para quem você quer transferir?", success: "Comprovante da operação" },
};

function el(id) { return document.getElementById(id); }

function setStep(step) {
    state.step = step;
    if (flow) flow.dataset.step = step;
    const subtitle = el("transfer-subtitle");
    if (subtitle) subtitle.textContent = SUBTITLES[MODE][step] ?? "";
    document.querySelectorAll("[data-step-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.stepPanel === step);
    });
}

function updateAmountDisplay() {
    const value = formatAmount(state.amountDigits);
    if (el("amount-display"))  el("amount-display").textContent  = value;
    if (el("selected-amount")) el("selected-amount").textContent = value;
    if (el("confirm-amount"))  el("confirm-amount").textContent  = value;
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

function writeReceipt() {
    if (el("receipt-amount")) el("receipt-amount").textContent = formatAmount(state.amountDigits);
    if (el("receipt-date"))   el("receipt-date").textContent   = new Date().toLocaleString("pt-BR");
    if (el("receipt-account")) el("receipt-account").textContent = getAccountLabel(state.accountType);
    if (el("receipt-name"))  el("receipt-name").textContent    = state.selectedName || "-";
}

// ── Deposit / Withdrawal ───────────────────────────────────────────────────────

function setupSimpleFlow() {
    const errorMap = {
        valor_invalido:   "Valor inválido.",
        sem_conta:        "Conta corrente não encontrada.",
        saldo_insuficiente: "Saldo insuficiente para este saque.",
    };

    async function submitAndCheck() {
        const form         = el("operacao-form");
        const hiddenAmount = el("hidden-amount");
        if (!form || !hiddenAmount) return;
        hiddenAmount.value = state.amountDigits || "0";

        const btn = el("btn-confirmar");
        if (btn) btn.disabled = true;

        try {
            const response = await fetch("/operacao", { method: "POST", body: new FormData(form) });
            const finalUrl = new URL(response.url);
            if (finalUrl.pathname === "/home") {
                writeReceipt();
                setStep("success");
            } else {
                const msg = errorMap[finalUrl.searchParams.get("error")] || "Erro ao realizar operação.";
                let errorDiv = el("inline-simple-error");
                if (!errorDiv) {
                    errorDiv = document.createElement("div");
                    errorDiv.id = "inline-simple-error";
                    errorDiv.className = "feedback-message feedback-error";
                    errorDiv.style.marginBottom = "1rem";
                    flow?.insertBefore(errorDiv, flow.querySelector(".transfer-header")?.nextSibling ?? null);
                }
                errorDiv.textContent = msg;
                errorDiv.style.display = "block";
                setTimeout(() => { errorDiv.style.display = "none"; }, 3000);
                setStep("confirm");
            }
        } catch {
            alert("Erro de conexão. Tente novamente.");
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    function advance() {
        if (state.step === "amount") {
            if (!state.amountDigits || Number(state.amountDigits) === 0) return;
            updateAmountDisplay();
            setStep("confirm");
        } else if (state.step === "confirm") {
            submitAndCheck();
        } else if (state.step === "success") {
            window.location.href = "/home";
        }
    }

    el("btn-amount-next")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) return;
        updateAmountDisplay();
        setStep("confirm");
    });
    el("btn-back-amount")?.addEventListener("click", () => setStep("amount"));
    el("btn-confirmar")?.addEventListener("click", () => submitAndCheck());
    el("btn-finish")?.addEventListener("click",      () => { window.location.href = "/home"; });
    el("btn-cancelar")?.addEventListener("click", () => {
        state.step === "confirm" ? setStep("amount") : (window.location.href = "/home");
    });

    wireNumpadKeyboard({ onDigit: appendDigit, onDelete: deleteDigit, onEnter: advance, onEscape: () => el("btn-cancelar")?.click() });
}

// ── Transfer ──────────────────────────────────────────────────────────────────

function setupTransferFlow() {
    function updateAccountDisplay() {
        const balanceData   = el("balance-data");
        const balanceDisplay = el("balance-display");
        const hiddenFrom    = el("hidden-from-account-type");
        if (balanceData && balanceDisplay) balanceDisplay.textContent = balanceData.dataset[state.accountType];
        if (hiddenFrom) hiddenFrom.value = state.accountType;
    }

    function setupOwnAccountButton() {
        const balanceData = el("balance-data");
        const btn = el("btn-own-account");
        if (!btn || !balanceData) return;
        const targetType    = state.accountType === "corrente" ? "poupanca" : "corrente";
        const targetId      = targetType === "corrente" ? balanceData.dataset.correnteId : balanceData.dataset.poupancaId;
        const targetLabel   = targetType === "corrente" ? "Conta Corrente" : "Conta Poupança";
        const targetInitial = targetType === "corrente" ? "CC" : "CP";
        btn.dataset.accountId = targetId;
        btn.dataset.name      = targetLabel;
        const nameEl    = el("own-account-name");
        const initialEl = el("own-account-initial");
        if (nameEl)    nameEl.textContent    = targetLabel;
        if (initialEl) initialEl.textContent = targetInitial;
    }

    function selectRecipient(card) {
        document.querySelectorAll(".recipient-card").forEach((c) => c.classList.remove("is-selected"));
        card.classList.add("is-selected");
        state.selectedAccountId = card.dataset.accountId;
        state.selectedName      = card.dataset.name;
        const btn = el("btn-to-success");
        if (btn) btn.disabled = false;
    }

    function filterRecipients(text) {
        const q = text.trim().toLowerCase();
        document.querySelectorAll("#recipient-grid .recipient-card").forEach((card) => {
            const name   = (card.dataset.name || "").toLowerCase();
            const number = card.querySelector(".recipient-bank")?.textContent.toLowerCase() || "";
            card.style.display = (!q || name.includes(q) || number.includes(q)) ? "" : "none";
        });
    }

    async function submitAndCheck() {
        const form         = el("operacao-form");
        const hiddenAmount = el("hidden-amount");
        const hiddenAcct   = el("hidden-to-account");
        const hiddenFrom   = el("hidden-from-account-type");
        if (!form || !hiddenAmount || !hiddenAcct) return;

        hiddenAmount.value = state.amountDigits || "0";
        hiddenAcct.value   = state.selectedAccountId || "";
        if (hiddenFrom) hiddenFrom.value = state.accountType;

        const btn = el("btn-to-success");
        if (btn) btn.disabled = true;

        const errorMap = {
            saldo_insuficiente:    "Saldo insuficiente para esta transferência.",
            valor_invalido:        "Valor de transferência inválido.",
            destinatario_invalido: "Destinatário não encontrado.",
            sem_conta:             "Nenhuma conta encontrada para o usuário.",
        };

        try {
            const response = await fetch("/operacao", { method: "POST", body: new FormData(form) });
            const finalUrl = new URL(response.url);
            if (finalUrl.pathname === "/home") {
                writeReceipt();
                setStep("success");
            } else {
                const msg = errorMap[finalUrl.searchParams.get("error")] || "Erro ao realizar transferência.";
                let errorDiv = el("inline-transfer-error");
                if (!errorDiv) {
                    errorDiv = document.createElement("div");
                    errorDiv.id = "inline-transfer-error";
                    errorDiv.className = "feedback-message feedback-error";
                    errorDiv.style.marginBottom = "1rem";
                    flow?.insertBefore(errorDiv, flow.querySelector(".transfer-header")?.nextSibling ?? null);
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

    // account tabs
    document.querySelectorAll(".transfer-account-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".transfer-account-tab").forEach((t) => t.classList.remove("is-active"));
            tab.classList.add("is-active");
            state.accountType = tab.dataset.account;
            updateAccountDisplay();
            setupOwnAccountButton();
        });
    });

    updateAccountDisplay();

    el("btn-amount-next")?.addEventListener("click", () => {
        if (!state.amountDigits || Number(state.amountDigits) === 0) return;
        setStep("recipient");
    });
    el("btn-back-amount")?.addEventListener("click", () => setStep("amount"));
    setupOwnAccountButton();
    el("btn-own-account")?.addEventListener("click", () => selectRecipient(el("btn-own-account")));
    el("recipient-search")?.addEventListener("input", (e) => filterRecipients(e.target.value));
    document.querySelectorAll(".recipient-card").forEach((card) => {
        card.addEventListener("click", () => selectRecipient(card));
    });
    el("btn-to-success")?.addEventListener("click", () => {
        if (!state.selectedAccountId) return;
        submitAndCheck();
    });
    el("btn-finish")?.addEventListener("click",   () => { window.location.href = "/home"; });
    el("btn-cancelar")?.addEventListener("click", () => {
        if (state.step === "amount" || state.step === "success") {
            window.location.href = "/home";
        } else {
            setStep("amount");
        }
    });

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
        onEscape: () => el("btn-cancelar")?.click(),
    });
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    updateAmountDisplay();

    document.querySelectorAll(".numpad-key[data-number]").forEach((btn) => {
        btn.addEventListener("click", () => appendDigit(btn.dataset.number));
    });
    el("btn-delete")?.addEventListener("click", deleteDigit);

    if (MODE === "transferir") {
        setupTransferFlow();
    } else {
        setupSimpleFlow();
    }
});
