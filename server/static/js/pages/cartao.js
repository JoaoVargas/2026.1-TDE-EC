import { initStatementFilters } from "../components/statement-filters.js";

function parseBrl(str) {
    const digits = str.replace(/\D/g, "");
    return parseInt(digits || "0", 10);
}

function formatBrl(cents) {
    return (cents / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function bindCurrencyInput(inputEl, hiddenEl) {
    inputEl.addEventListener("input", () => {
        const cents = parseBrl(inputEl.value);
        inputEl.value = formatBrl(cents);
        if (hiddenEl) hiddenEl.value = cents;
    });
    inputEl.addEventListener("focus", () => {
        if (inputEl.value === "" || inputEl.value === formatBrl(0)) inputEl.value = "";
    });
}

// ── Modal helpers ───────────────────────────────────────────────────────────
function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.hidden = false;
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.hidden = true;
}

document.addEventListener("DOMContentLoaded", () => {
    // Filters — shared logic + description search
    let searchText = "";
    const { applyAll } = initStatementFilters({
        navSelector:  "#cartao-filters",
        listSelector: "#cartao-statement-list",
        countPillId:  "cartao-count",
        extraTest: (item) => !searchText || (item.dataset.title || "").includes(searchText),
    });

    const searchInput = document.getElementById("cartao-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            searchText = searchInput.value.trim().toLowerCase();
            applyAll();
        });
    }

    // Pay bill modal
    const btnPagar    = document.getElementById("btn-pagar-fatura");
    const pagarDisplay = document.getElementById("pagar-amount-display");
    const pagarHidden  = document.getElementById("pagar-amount-cents");
    if (btnPagar) btnPagar.addEventListener("click", () => openModal("modal-pagar"));
    if (pagarDisplay && pagarHidden) bindCurrencyInput(pagarDisplay, pagarHidden);

    const btnPagarTotal = document.getElementById("btn-pagar-total");
    if (btnPagarTotal && pagarDisplay && pagarHidden) {
        btnPagarTotal.addEventListener("click", () => {
            const full = parseInt(btnPagarTotal.dataset.full || "0", 10);
            pagarHidden.value  = full;
            pagarDisplay.value = formatBrl(full);
        });
    }

    // Simulate purchase modal
    const btnCompra    = document.getElementById("btn-simular-compra");
    const compraDisplay = document.getElementById("compra-amount-display");
    const compraHidden  = document.getElementById("compra-amount-cents");
    if (btnCompra) btnCompra.addEventListener("click", () => openModal("modal-compra"));
    if (compraDisplay && compraHidden) bindCurrencyInput(compraDisplay, compraHidden);

    // Adjust limit modal
    const btnLimite  = document.getElementById("btn-ajustar-limite");
    const slider     = document.getElementById("limite-slider");
    const limDisplay = document.getElementById("limite-display");
    const limHidden  = document.getElementById("limite-hidden");

    if (btnLimite) btnLimite.addEventListener("click", () => openModal("modal-limite"));

    if (slider && limDisplay && limHidden) {
        const usedBrl = parseInt(slider.dataset.used || "0", 10);
        const minVal  = Math.max(100, Math.ceil(usedBrl / 100) * 100);
        slider.min = minVal;

        function updateSlider() {
            const brl = parseInt(slider.value, 10);
            limDisplay.textContent = (brl).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
            limHidden.value = brl * 100;
        }
        slider.addEventListener("input", updateSlider);
        updateSlider();
    }

    // Close buttons
    document.querySelectorAll("[data-modal-close]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const backdrop = btn.closest(".management-modal-backdrop");
            if (backdrop) backdrop.hidden = true;
        });
    });
    document.querySelectorAll(".management-modal-backdrop").forEach((backdrop) => {
        backdrop.addEventListener("click", (e) => {
            if (e.target === backdrop) backdrop.hidden = true;
        });
    });
});
