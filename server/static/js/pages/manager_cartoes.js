import { createModal } from "../components/modal.js";

function parseBrl(str) {
    return Math.round(parseFloat(str.replace(/\./g, "").replace(",", ".").replace(/[^0-9.]/g, "")) * 100) || 0;
}

function formatBrl(cents) {
    return (cents / 100).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

document.addEventListener("DOMContentLoaded", () => {
    const cancelModal = createModal("cancel-card-modal");
    const limitModal  = createModal("limit-card-modal");
    const createModal_ = createModal("create-card-modal");

    // ── Cancel card ──────────────────────────────────────────
    document.querySelectorAll(".management-cancel-card-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form = document.getElementById("cancel-card-form");
            const desc = document.getElementById("cancel-card-desc");
            form.action = `/manager/cartoes/${btn.dataset.cardId}/cancelar`;
            cancelModal.open({
                trigger: btn,
                onOpen() {
                    if (desc) desc.textContent = `Cancelar cartão de: ${btn.dataset.userName || ""}`;
                },
            });
        });
    });

    // ── Adjust limit ─────────────────────────────────────────
    const limitSlider  = document.getElementById("limit-card-slider");
    const limitCentsEl = document.getElementById("limit-card-cents");
    const limitDisplay = document.getElementById("limit-card-display");

    function updateLimitDisplay() {
        const val = parseInt(limitSlider.value, 10);
        limitCentsEl.value = val;
        limitDisplay.textContent = "R$ " + formatBrl(val);
    }

    if (limitSlider) {
        limitSlider.addEventListener("input", updateLimitDisplay);
    }

    document.querySelectorAll(".management-limit-card-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form     = document.getElementById("limit-card-form");
            const subtitle = document.getElementById("limit-card-subtitle");
            const usedCents  = parseInt(btn.dataset.usedCents, 10) || 0;
            const limitCents = parseInt(btn.dataset.limitCents, 10) || 500000;

            // clamp slider min to the next R$1000 above used amount
            const step = 100000;
            const minCents = Math.max(step, Math.ceil(usedCents / step) * step);
            limitSlider.min   = minCents;
            limitSlider.value = Math.max(limitCents, minCents);

            form.action = `/manager/cartoes/${btn.dataset.cardId}/limite`;
            limitModal.open({
                trigger: btn,
                onOpen() {
                    if (subtitle) subtitle.textContent = `Cliente: ${btn.dataset.userName || ""}`;
                    updateLimitDisplay();
                    setTimeout(() => limitSlider?.focus(), 0);
                },
            });
        });
    });

    // ── Create card ──────────────────────────────────────────
    const createLimitDisplay = document.getElementById("create-card-limit-display");
    const createLimitCents   = document.getElementById("create-card-limit-cents");
    const userId             = document.getElementById("create-card-user-id");

    if (createLimitDisplay) {
        createLimitDisplay.value = formatBrl(500000);
        createLimitDisplay.addEventListener("blur", () => {
            const cents = parseBrl(createLimitDisplay.value);
            createLimitCents.value = cents;
            createLimitDisplay.value = formatBrl(cents);
        });
    }

    document.querySelectorAll(".management-create-card-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const subtitle = document.getElementById("create-card-subtitle");
            createModal_.open({
                trigger: btn,
                onOpen() {
                    if (userId) userId.value = btn.dataset.userId || "";
                    if (subtitle) subtitle.textContent = `Cliente: ${btn.dataset.userName || ""}`;
                    if (createLimitDisplay) { createLimitDisplay.value = formatBrl(500000); createLimitCents.value = 500000; }
                    setTimeout(() => createLimitDisplay?.focus(), 0);
                },
            });
        });
    });
});
