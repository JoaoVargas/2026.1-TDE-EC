export function createModal(backdropId) {
    const backdrop = document.getElementById(backdropId);
    if (!backdrop) return null;

    let returnFocusEl = null;

    function close() {
        backdrop.hidden = true;
        returnFocusEl?.focus();
        returnFocusEl = null;
    }

    function open({ trigger = null, onOpen = null } = {}) {
        returnFocusEl = trigger;
        backdrop.hidden = false;
        onOpen?.();
    }

    backdrop.querySelectorAll("[data-modal-close]").forEach((btn) => {
        btn.addEventListener("click", close);
    });

    backdrop.addEventListener("click", (e) => {
        if (e.target === backdrop) close();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !backdrop.hidden) close();
    });

    return { open, close };
}
