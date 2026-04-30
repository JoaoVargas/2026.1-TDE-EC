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
    document.querySelectorAll(".management-name-edit-trigger").forEach((btn) => {
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

document.addEventListener("DOMContentLoaded", () => {
    bindModalEvents();
    bindEditButtons();
});
