const renameContext = {
    userId: null,
    nameEl: null,
    triggerEl: null,
};

function getBackdrop() {
    return document.getElementById("rename-modal-backdrop");
}

function getInput() {
    return document.getElementById("rename-modal-input");
}

function getRenameForm() {
    return document.getElementById("rename-form");
}

function openRenameModal(userId, currentName, nameEl, triggerEl) {
    const backdrop = getBackdrop();
    const input = getInput();
    const form = getRenameForm();
    if (!backdrop || !input || !form) return;

    renameContext.userId = userId;
    renameContext.nameEl = nameEl;
    renameContext.triggerEl = triggerEl;

    form.action = `/manager/accounts/${userId}/rename`;
    input.value = currentName || "";
    backdrop.hidden = false;

    setTimeout(() => {
        input.focus();
        input.select();
    }, 0);
}

function closeRenameModal() {
    const backdrop = getBackdrop();
    if (backdrop) backdrop.hidden = true;

    const triggerEl = renameContext.triggerEl;
    renameContext.userId = null;
    renameContext.nameEl = null;
    renameContext.triggerEl = null;
    triggerEl?.focus();
}

function bindEditButtons() {
    document.querySelectorAll(".management-name-edit-trigger:not(.management-cpf-edit-trigger):not(.management-addr-edit-trigger)").forEach((btn) => {
        const userId = btn.dataset.userId;
        const currentName = btn.dataset.userName;
        const nameEl = document.getElementById(`name-${userId}`);
        btn.addEventListener("click", () => openRenameModal(userId, currentName, nameEl, btn));
    });
}

function bindModalEvents() {
    const backdrop = getBackdrop();
    const closeBtn = document.getElementById("rename-modal-close");
    const cancelBtn = document.getElementById("rename-modal-cancel");
    const input = getInput();

    if (!backdrop || !closeBtn || !cancelBtn || !input) return;

    closeBtn.addEventListener("click", closeRenameModal);
    cancelBtn.addEventListener("click", closeRenameModal);

    backdrop.addEventListener("click", (event) => {
        if (event.target === backdrop) closeRenameModal();
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeRenameModal();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !backdrop.hidden) closeRenameModal();
    });
}

// ── CPF Modal ────────────────────────────────────────
function openCpfModal(userId, currentCpf, triggerEl) {
    const backdrop = document.getElementById("cpf-modal-backdrop");
    const form = document.getElementById("cpf-form");
    const input = document.getElementById("cpf-modal-input");
    if (!backdrop || !form || !input) return;

    form.action = `/manager/accounts/${userId}/cpf`;
    input.value = currentCpf || "";
    backdrop.hidden = false;
    backdrop._triggerEl = triggerEl;
    setTimeout(() => { input.focus(); input.select(); }, 0);
}

function closeCpfModal() {
    const backdrop = document.getElementById("cpf-modal-backdrop");
    if (!backdrop) return;
    backdrop.hidden = true;
    backdrop._triggerEl?.focus();
}

function bindCpfModalEvents() {
    const backdrop = document.getElementById("cpf-modal-backdrop");
    const closeBtn = document.getElementById("cpf-modal-close");
    const cancelBtn = document.getElementById("cpf-modal-cancel");
    if (!backdrop || !closeBtn || !cancelBtn) return;

    closeBtn.addEventListener("click", closeCpfModal);
    cancelBtn.addEventListener("click", closeCpfModal);
    backdrop.addEventListener("click", (e) => { if (e.target === backdrop) closeCpfModal(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !backdrop.hidden) closeCpfModal(); });
}

function bindCpfEditButtons() {
    document.querySelectorAll(".management-cpf-edit-trigger").forEach((btn) => {
        btn.addEventListener("click", () => openCpfModal(btn.dataset.userId, btn.dataset.userCpf, btn));
    });
}

// ── Address Modal ─────────────────────────────────────
function openAddrModal(userId, data, triggerEl) {
    const backdrop = document.getElementById("addr-modal-backdrop");
    const form = document.getElementById("addr-form");
    if (!backdrop || !form) return;

    form.action = `/manager/accounts/${userId}/endereco`;
    document.getElementById("addr-modal-cep").value          = data.cep          || "";
    document.getElementById("addr-modal-street").value       = data.street       || "";
    document.getElementById("addr-modal-number").value       = data.number       || "";
    document.getElementById("addr-modal-neighborhood").value = data.neighborhood || "";
    document.getElementById("addr-modal-city").value         = data.city         || "";
    document.getElementById("addr-modal-state").value        = data.state        || "";
    backdrop.hidden = false;
    backdrop._triggerEl = triggerEl;
    setTimeout(() => document.getElementById("addr-modal-cep").focus(), 0);
}

function closeAddrModal() {
    const backdrop = document.getElementById("addr-modal-backdrop");
    if (!backdrop) return;
    backdrop.hidden = true;
    backdrop._triggerEl?.focus();
}

function bindAddrModalEvents() {
    const backdrop = document.getElementById("addr-modal-backdrop");
    const closeBtn = document.getElementById("addr-modal-close");
    const cancelBtn = document.getElementById("addr-modal-cancel");
    if (!backdrop || !closeBtn || !cancelBtn) return;

    closeBtn.addEventListener("click", closeAddrModal);
    cancelBtn.addEventListener("click", closeAddrModal);
    backdrop.addEventListener("click", (e) => { if (e.target === backdrop) closeAddrModal(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !backdrop.hidden) closeAddrModal(); });
}

function bindAddrEditButtons() {
    document.querySelectorAll(".management-addr-edit-trigger").forEach((btn) => {
        btn.addEventListener("click", () => openAddrModal(btn.dataset.userId, {
            cep:          btn.dataset.cep,
            street:       btn.dataset.street,
            number:       btn.dataset.number,
            neighborhood: btn.dataset.neighborhood,
            city:         btn.dataset.city,
            state:        btn.dataset.state,
        }, btn));
    });
}

document.addEventListener("DOMContentLoaded", () => {
    bindModalEvents();
    bindEditButtons();
    bindCpfModalEvents();
    bindCpfEditButtons();
    bindAddrModalEvents();
    bindAddrEditButtons();
});
