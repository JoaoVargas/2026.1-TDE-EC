export function showFieldError(input, message) {
    const group = input.closest(".form-group");
    if (!group) {
        return;
    }

    let errorEl = group.querySelector(".erro-campo");
    if (!errorEl) {
        errorEl = document.createElement("span");
        errorEl.className = "erro-campo";
        group.appendChild(errorEl);
    }

    if (message) {
        errorEl.textContent = message;
        input.classList.add("input-erro");
        input.classList.remove("input-ok");
        return;
    }

    errorEl.textContent = "";
    input.classList.remove("input-erro");
    input.classList.add("input-ok");
}

export function showGlobalMessage(target, text, type) {
    target.textContent = text;
    const variantClass = type === "sucesso" ? "feedback-success" : "feedback-error";
    target.className = `feedback-message mensagem ${type} ${variantClass}`;
    target.style.display = "block";
    window.setTimeout(() => {
        target.style.display = "none";
    }, 5000);
}
