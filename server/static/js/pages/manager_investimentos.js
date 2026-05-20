import { createModal } from "../components/modal.js";

document.addEventListener("DOMContentLoaded", () => {
    // ── Modal: Atualizar cotação ──────────────────────────────────
    const cotacaoModal = createModal("cotacao-modal-backdrop");
    const cotacaoForm  = document.getElementById("cotacao-form");
    const priceInput   = document.getElementById("cotacao-price-input");
    const codeSpan     = document.getElementById("cotacao-modal-code");
    const statusEl     = document.getElementById("cotacao-api-status");
    const buscarBtn    = document.getElementById("cotacao-buscar-btn");

    let currentPortfolioId = null;

    document.querySelectorAll(".minv-cotacao-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentPortfolioId = btn.dataset.portfolioId;
            cotacaoForm.action = `/manager/investimentos/${currentPortfolioId}/cotacao`;
            codeSpan.textContent = `${btn.dataset.stockName} (${btn.dataset.stockCode})`;
            statusEl.textContent = "";
            statusEl.className = "management-modal-feedback";
            cotacaoModal.open({
                trigger: btn,
                onOpen() {
                    priceInput.value = parseFloat(btn.dataset.currentPrice).toFixed(2).replace(".", ",");
                    setTimeout(() => { priceInput.focus(); priceInput.select(); }, 0);
                },
            });
        });
    });

    buscarBtn?.addEventListener("click", () => {
        if (!currentPortfolioId) return;
        statusEl.textContent = "Buscando cotação...";
        statusEl.className = "management-modal-feedback";
        buscarBtn.disabled = true;

        fetch(`/manager/investimentos/${currentPortfolioId}/cotacao-api`)
            .then((r) => r.json())
            .then((data) => {
                if (data.error) {
                    statusEl.textContent = "Não foi possível buscar online: " + data.error;
                    statusEl.className = "management-modal-feedback is-error";
                } else {
                    priceInput.value = parseFloat(data.price).toFixed(2).replace(".", ",");
                    statusEl.textContent = "Cotação obtida com sucesso!";
                    statusEl.className = "management-modal-feedback is-success";
                }
            })
            .catch(() => {
                statusEl.textContent = "Erro ao buscar cotação online.";
                statusEl.className = "management-modal-feedback is-error";
            })
            .finally(() => { buscarBtn.disabled = false; });
    });

    // ── Modal: Excluir carteira ───────────────────────────────────
    const deletarModal = createModal("deletar-modal-backdrop");
    const deletarForm  = document.getElementById("deletar-form");
    const deletarDesc  = document.getElementById("deletar-modal-desc");

    document.querySelectorAll(".minv-deletar-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            deletarForm.action = `/manager/investimentos/${btn.dataset.portfolioId}/deletar`;
            deletarDesc.textContent = `Tem certeza que deseja encerrar a carteira "${btn.dataset.stockName} (${btn.dataset.stockCode})"?`;
            deletarModal.open({ trigger: btn });
        });
    });
});
