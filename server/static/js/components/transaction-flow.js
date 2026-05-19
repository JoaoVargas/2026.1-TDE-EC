/**
 * Wires physical keyboard input to a numpad-based flow.
 * Ignored when focus is on an input or textarea.
 *
 * @param {{ onDigit: (key: string) => void, onDelete: () => void, onEnter?: () => void, onEscape?: () => void }} config
 */
export function wireNumpadKeyboard({ onDigit, onDelete, onEnter, onEscape }) {
    document.addEventListener("keydown", (e) => {
        if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
        if (e.key >= "0" && e.key <= "9") {
            e.preventDefault();
            onDigit(e.key);
        } else if (e.key === "Backspace") {
            e.preventDefault();
            onDelete();
        } else if (e.key === "Enter") {
            e.preventDefault();
            onEnter?.();
        } else if (e.key === "Escape") {
            e.preventDefault();
            onEscape?.();
        }
    });
}

export function formatAmount(digits) {
    const cents = Number(digits || "0");
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function getAccountLabel(accountType) {
    return accountType === "poupanca" ? "Conta Poupança" : "Conta Corrente";
}

/**
 * Creates and wires a numpad-based transaction flow (deposit/withdrawal).
 *
 * @param {{
 *   subtitles: { amount: string, confirm: string, success: string },
 *   formId: string
 * }} config
 */
export function createNumpadFlow({ subtitles, formId }) {
    const state = {
        step: "amount",
        amountDigits: "",
        accountType: localStorage.getItem("conta_selecionada") || "corrente",
    };

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
        if (subtitle) subtitle.textContent = subtitles[step] ?? "";
        document.querySelectorAll("[data-step-panel]").forEach((panel) => {
            panel.classList.toggle("is-active", panel.dataset.stepPanel === step);
        });
    }

    function updateAmountDisplay() {
        const value = formatAmount(state.amountDigits);
        const el = (id) => document.getElementById(id);
        if (el("amount-display")) el("amount-display").textContent = value;
        if (el("selected-amount")) el("selected-amount").textContent = value;
        if (el("confirm-amount")) el("confirm-amount").textContent = value;
    }

    function populateConfirmStep() {
        updateAmountDisplay();
        const label = document.getElementById("confirm-account-label");
        if (label) label.textContent = `Destino: ${getAccountLabel(state.accountType)}`;
    }

    function writeReceipt() {
        const el = (id) => document.getElementById(id);
        if (el("receipt-amount")) el("receipt-amount").textContent = formatAmount(state.amountDigits);
        if (el("receipt-date")) el("receipt-date").textContent = new Date().toLocaleString("pt-BR");
        if (el("receipt-account")) el("receipt-account").textContent = getAccountLabel(state.accountType);
    }

    function submitForm() {
        const form = document.getElementById(formId);
        const hiddenAmount = document.getElementById("hidden-amount");
        const hiddenAccountType = document.getElementById("hidden-account-type");
        if (!form || !hiddenAmount) return;
        hiddenAmount.value = state.amountDigits || "0";
        if (hiddenAccountType) hiddenAccountType.value = state.accountType;
        form.submit();
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

    function advanceStep() {
        if (state.step === "amount") {
            if (!state.amountDigits || Number(state.amountDigits) === 0) return;
            populateConfirmStep();
            setStep("confirm");
        } else if (state.step === "confirm") {
            writeReceipt();
            setStep("success");
            submitForm();
        } else if (state.step === "success") {
            window.location.href = "/home";
        }
    }

    function init() {
        updateAmountDisplay();
        updateAccountDisplay();

        document.querySelectorAll(".numpad-key[data-number]").forEach((button) => {
            button.addEventListener("click", () => appendDigit(button.dataset.number));
        });

        document.getElementById("btn-delete")?.addEventListener("click", deleteDigit);

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
            submitForm();
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

        wireNumpadKeyboard({
            onDigit: appendDigit,
            onDelete: deleteDigit,
            onEnter: advanceStep,
            onEscape: () => document.getElementById("btn-cancelar")?.click(),
        });
    }

    return { init };
}
