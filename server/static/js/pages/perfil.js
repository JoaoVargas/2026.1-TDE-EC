import { createModal } from "../components/modal.js";
import { wireCepLookup } from "../components/cep-lookup.js";

document.addEventListener("DOMContentLoaded", () => {
    wireCepLookup({
        cepInput:          document.getElementById("perfil-addr-cep"),
        streetInput:       document.getElementById("perfil-addr-street"),
        neighborhoodInput: document.getElementById("perfil-addr-neighborhood"),
        cityInput:         document.getElementById("perfil-addr-city"),
        stateInput:        document.getElementById("perfil-addr-state"),
        numberInput:       document.getElementById("perfil-addr-number"),
    });
    const profileModal = createModal("perfil-profile-modal-backdrop");
    const addrModal    = createModal("perfil-addr-modal-backdrop");

    document.querySelector(".perfil-profile-trigger")?.addEventListener("click", (e) => {
        const btn = e.currentTarget;
        profileModal.open({
            trigger: btn,
            onOpen() {
                const nameInput = document.getElementById("perfil-profile-name");
                document.getElementById("perfil-profile-email").value = btn.dataset.email || "";
                nameInput.value = btn.dataset.name || "";
                setTimeout(() => { nameInput.focus(); nameInput.select(); }, 0);
            },
        });
    });

    document.querySelector(".perfil-addr-trigger")?.addEventListener("click", (e) => {
        const btn = e.currentTarget;
        addrModal.open({
            trigger: btn,
            onOpen() {
                document.getElementById("perfil-addr-cep").value          = btn.dataset.cep          || "";
                document.getElementById("perfil-addr-street").value       = btn.dataset.street       || "";
                document.getElementById("perfil-addr-number").value       = btn.dataset.number       || "";
                document.getElementById("perfil-addr-neighborhood").value = btn.dataset.neighborhood || "";
                document.getElementById("perfil-addr-city").value         = btn.dataset.city         || "";
                document.getElementById("perfil-addr-state").value        = btn.dataset.state        || "";
                setTimeout(() => document.getElementById("perfil-addr-cep").focus(), 0);
            },
        });
    });
});
