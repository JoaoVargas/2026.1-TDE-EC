import { createModal } from "../components/modal.js";

const segurosCard = document.querySelector('bb-insight-card[data-modal-id="modal-seguros"]');
const termosCard  = document.querySelector('bb-insight-card[data-modal-id="modal-termos"]');

const segurosModal = createModal("modal-seguros");
const termosModal  = createModal("modal-termos");

function wireCardButton(card, modal) {
    if (!card || !modal) return;
    const btn = card.querySelector("button");
    if (btn) btn.addEventListener("click", () => modal.open({ trigger: btn }));
}

wireCardButton(segurosCard, segurosModal);
wireCardButton(termosCard, termosModal);
