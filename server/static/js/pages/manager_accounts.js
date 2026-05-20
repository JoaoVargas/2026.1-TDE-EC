import { createModal } from "../components/modal.js";
import { wireCepLookup } from "../components/cep-lookup.js";

document.addEventListener("DOMContentLoaded", () => {
    wireCepLookup({
        cepInput:          document.getElementById("addr-modal-cep"),
        streetInput:       document.getElementById("addr-modal-street"),
        neighborhoodInput: document.getElementById("addr-modal-neighborhood"),
        cityInput:         document.getElementById("addr-modal-city"),
        stateInput:        document.getElementById("addr-modal-state"),
        numberInput:       document.getElementById("addr-modal-number"),
    });
    const profileModal = createModal("profile-modal-backdrop");
    const cpfModal     = createModal("cpf-modal-backdrop");
    const addrModal    = createModal("addr-modal-backdrop");

    // ── Profile (name + email) ────────────────────────────────
    document.querySelectorAll(".management-profile-edit-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form       = document.getElementById("profile-form");
            const nameInput  = document.getElementById("profile-modal-name");
            const emailInput = document.getElementById("profile-modal-email");
            form.action = `/manager/accounts/${btn.dataset.userId}/profile`;
            profileModal.open({
                trigger: btn,
                onOpen() {
                    nameInput.value  = btn.dataset.userName  || "";
                    emailInput.value = btn.dataset.userEmail || "";
                    setTimeout(() => { nameInput.focus(); nameInput.select(); }, 0);
                },
            });
        });
    });

    // ── CPF ───────────────────────────────────────────────────
    document.querySelectorAll(".management-cpf-edit-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form  = document.getElementById("cpf-form");
            const input = document.getElementById("cpf-modal-input");
            form.action = `/manager/accounts/${btn.dataset.userId}/cpf`;
            cpfModal.open({
                trigger: btn,
                onOpen() {
                    input.value = btn.dataset.userCpf || "";
                    setTimeout(() => { input.focus(); input.select(); }, 0);
                },
            });
        });
    });

    // ── Address ───────────────────────────────────────────────
    document.querySelectorAll(".management-addr-edit-trigger").forEach((btn) => {
        btn.addEventListener("click", () => {
            const form = document.getElementById("addr-form");
            form.action = `/manager/accounts/${btn.dataset.userId}/endereco`;
            addrModal.open({
                trigger: btn,
                onOpen() {
                    document.getElementById("addr-modal-cep").value          = btn.dataset.cep          || "";
                    document.getElementById("addr-modal-street").value       = btn.dataset.street       || "";
                    document.getElementById("addr-modal-number").value       = btn.dataset.number       || "";
                    document.getElementById("addr-modal-neighborhood").value = btn.dataset.neighborhood || "";
                    document.getElementById("addr-modal-city").value         = btn.dataset.city         || "";
                    document.getElementById("addr-modal-state").value        = btn.dataset.state        || "";
                    setTimeout(() => document.getElementById("addr-modal-cep").focus(), 0);
                },
            });
        });
    });
});
