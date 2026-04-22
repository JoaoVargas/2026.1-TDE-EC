import { requireManagerUser } from "/static/js/components/auth-token-guard.js";

const USERS_ACCOUNTS_ENDPOINT = "/api/management/users-accounts";
const USER_NAME_ENDPOINT = (userId) => `/api/management/users/${userId}/name`;

const renameContext = {
    user: null,
    nameEl: null,
    triggerEl: null,
};

function getToken() {
    return localStorage.getItem("token");
}

function getGrid() {
    return document.getElementById("management-users-grid");
}

function getLoader() {
    return document.getElementById("management-loader");
}

function getEmptyCard() {
    return document.getElementById("management-empty");
}

function getRenameModalBackdrop() {
    return document.getElementById("rename-modal-backdrop");
}

function getRenameModalInput() {
    return document.getElementById("rename-modal-input");
}

function getRenameModalFeedback() {
    return document.getElementById("rename-modal-feedback");
}

function getRenameModalSave() {
    return document.getElementById("rename-modal-save");
}

function getRenameModalCancel() {
    return document.getElementById("rename-modal-cancel");
}

function getRenameModalClose() {
    return document.getElementById("rename-modal-close");
}

function formatCpf(cpf) {
    if (!cpf) {
        return "-";
    }

    const digits = cpf.replace(/\D/g, "").padStart(11, "0").slice(-11);
    return digits
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
}

function formatMoney(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
        return "R$ 0,00";
    }

    return numeric.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function humanizeTipoUsuario(tipoUsuario) {
    return tipoUsuario === "manager" ? "Gerente" : "Cliente";
}

function humanizeTipoConta(tipoConta) {
    return tipoConta === "savings" ? "Poupanca" : "Corrente";
}

function showFeedback(message, kind = "neutral") {
    const feedback = document.getElementById("manager-feedback");
    if (!feedback) {
        return;
    }

    feedback.textContent = message;
    feedback.classList.remove("is-error", "is-success");

    if (kind === "error") {
        feedback.classList.add("is-error");
    }
    if (kind === "success") {
        feedback.classList.add("is-success");
    }
}

function setLoadingState(isLoading) {
    const loader = getLoader();
    if (loader) {
        loader.hidden = !isLoading;
    }
}

function setEmptyState(isEmpty) {
    const emptyCard = getEmptyCard();
    if (emptyCard) {
        emptyCard.hidden = !isEmpty;
    }
}

function setGridVisibility(show) {
    const grid = getGrid();
    if (!grid) {
        return;
    }

    grid.hidden = !show;
}

function createAccountRow(account) {
    const item = document.createElement("li");
    item.className = "management-account-item";

    const details = document.createElement("div");
    const number = document.createElement("strong");
    const accountMeta = document.createElement("p");
    const balance = document.createElement("span");

    const type = humanizeTipoConta(account.tipo_conta);
    number.textContent = account.numero_conta || "-";
    accountMeta.textContent = `Agencia ${account.agencia || "-"} - ${type}`;
    balance.textContent = formatMoney(account.saldo);

    details.append(number, accountMeta);
    item.append(details, balance);

    return item;
}

function createMetaItem(label, value) {
    const item = document.createElement("span");
    const strong = document.createElement("strong");

    strong.textContent = `${label}: `;
    item.append(strong, value);
    return item;
}

function setInlineFeedback(messageEl, message, kind = "neutral") {
    if (!messageEl) {
        return;
    }

    messageEl.textContent = message;
    messageEl.classList.remove("is-error", "is-success");

    if (kind === "error") {
        messageEl.classList.add("is-error");
    }
    if (kind === "success") {
        messageEl.classList.add("is-success");
    }
}

function setRenameModalFeedback(message, kind = "neutral") {
    const feedback = getRenameModalFeedback();
    if (!feedback) {
        return;
    }

    setInlineFeedback(feedback, message, kind);
}

function setRenameModalBusyState(isBusy) {
    const saveBtn = getRenameModalSave();
    const cancelBtn = getRenameModalCancel();
    const closeBtn = getRenameModalClose();

    if (saveBtn) {
        saveBtn.disabled = isBusy;
        saveBtn.textContent = isBusy ? "Salvando..." : "Salvar";
    }
    if (cancelBtn) {
        cancelBtn.disabled = isBusy;
    }
    if (closeBtn) {
        closeBtn.disabled = isBusy;
    }
}

function openRenameModal(user, nameEl, triggerEl) {
    const backdrop = getRenameModalBackdrop();
    const input = getRenameModalInput();
    if (!backdrop || !input) {
        return;
    }

    renameContext.user = user;
    renameContext.nameEl = nameEl;
    renameContext.triggerEl = triggerEl;

    input.value = user?.nome || "";
    setRenameModalFeedback("");
    setRenameModalBusyState(false);
    backdrop.hidden = false;

    setTimeout(() => {
        input.focus();
        input.select();
    }, 0);
}

function closeRenameModal() {
    const backdrop = getRenameModalBackdrop();
    if (backdrop) {
        backdrop.hidden = true;
    }

    setRenameModalFeedback("");
    setRenameModalBusyState(false);

    const triggerEl = renameContext.triggerEl;
    renameContext.user = null;
    renameContext.nameEl = null;
    renameContext.triggerEl = null;
    triggerEl?.focus();
}

async function submitRenameModal() {
    if (!renameContext.user || !renameContext.nameEl) {
        closeRenameModal();
        return;
    }

    const input = getRenameModalInput();
    if (!input) {
        closeRenameModal();
        return;
    }

    const nextName = input.value.trim();
    if (!nextName) {
        setRenameModalFeedback("Informe um nome valido.", "error");
        input.focus();
        return;
    }

    setRenameModalBusyState(true);
    setRenameModalFeedback("Salvando nome...");

    const result = await updateUserName(renameContext.user.id, nextName);

    if (result.status === 401) {
        window.location.href = "/login";
        return;
    }

    if (result.status === 403) {
        window.location.href = "/home";
        return;
    }

    if (!result.ok) {
        setRenameModalFeedback(result.detail, "error");
        setRenameModalBusyState(false);
        return;
    }

    const updatedName = result.payload?.nome || nextName;
    renameContext.user.nome = updatedName;
    renameContext.nameEl.textContent = updatedName;
    showFeedback(`Nome do usuario ${renameContext.user.id} atualizado.`, "success");
    closeRenameModal();
}

function bindRenameModalEvents() {
    const backdrop = getRenameModalBackdrop();
    const closeBtn = getRenameModalClose();
    const cancelBtn = getRenameModalCancel();
    const saveBtn = getRenameModalSave();
    const input = getRenameModalInput();

    if (!backdrop || !closeBtn || !cancelBtn || !saveBtn || !input) {
        return;
    }

    closeBtn.addEventListener("click", closeRenameModal);
    cancelBtn.addEventListener("click", closeRenameModal);
    saveBtn.addEventListener("click", submitRenameModal);

    backdrop.addEventListener("click", (event) => {
        if (event.target === backdrop) {
            closeRenameModal();
        }
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            submitRenameModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        if (!backdrop.hidden) {
            closeRenameModal();
        }
    });
}

function createPenIcon() {
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("viewBox", "0 0 24 24");
    icon.setAttribute("aria-hidden", "true");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute(
        "d",
        "M3 17.25V21h3.75l11-11-3.75-3.75-11 11zM20.71 7.04a1.003 1.003 0 000-1.42l-2.34-2.34a1.003 1.003 0 00-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z",
    );

    icon.appendChild(path);
    return icon;
}

async function updateUserName(userId, nome) {
    const token = getToken();
    if (!token) {
        return { ok: false, status: 401, detail: "Nao autenticado." };
    }

    try {
        const response = await fetch(USER_NAME_ENDPOINT(userId), {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ nome }),
        });

        let payload = {};
        try {
            payload = await response.json();
        } catch {
            payload = {};
        }

        return {
            ok: response.ok,
            status: response.status,
            payload,
            detail: payload?.detail || "Nao foi possivel atualizar o nome.",
        };
    } catch {
        return { ok: false, status: 0, detail: "Erro de rede ao atualizar o nome." };
    }
}

function createUserCard(user) {
    const card = document.createElement("article");
    card.className = "management-user-card ui-card";

    const accounts = user.contas ?? [];
    const accountItems = document.createElement("ul");
    accountItems.className = "management-account-list";

    if (!accounts.length) {
        const empty = document.createElement("li");
        empty.className = "management-account-empty";
        empty.textContent = "Nenhuma conta vinculada.";
        accountItems.appendChild(empty);
    } else {
        accounts.forEach((account) => {
            accountItems.appendChild(createAccountRow(account));
        });
    }

    const perfil = humanizeTipoUsuario(user.tipo_usuario);
    const header = document.createElement("header");
    header.className = "management-user-header";

    const identity = document.createElement("div");
    identity.className = "management-user-identity";
    const nameRow = document.createElement("div");
    nameRow.className = "management-user-name-row";
    const name = document.createElement("h2");
    const email = document.createElement("p");
    const badge = document.createElement("span");
    const editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "management-name-edit-trigger";
    editBtn.title = "Alterar nome";
    editBtn.append(createPenIcon());

    const editLabel = document.createElement("span");
    editLabel.textContent = "Editar";
    editBtn.append(editLabel);

    name.textContent = user.nome || "Usuario";
    email.textContent = user.email || "-";
    badge.className = "management-badge";
    badge.textContent = perfil;

    nameRow.append(name, editBtn);
    identity.append(nameRow, email);
    header.append(identity, badge);

    const meta = document.createElement("div");
    meta.className = "management-user-meta";
    meta.append(
        createMetaItem("ID", `${user.id ?? "-"}`),
        createMetaItem("CPF", formatCpf(user.cpf)),
        createMetaItem("Contas", `${accounts.length}`),
    );

    editBtn.addEventListener("click", () => {
        openRenameModal(user, name, editBtn);
    });

    card.append(header, meta);

    card.appendChild(accountItems);
    return card;
}

function renderUsers(users) {
    const grid = getGrid();
    if (!grid) {
        return;
    }

    grid.innerHTML = "";

    if (!users.length) {
        setGridVisibility(false);
        setEmptyState(true);
        showFeedback("Nenhum usuario encontrado.");
        return;
    }

    setGridVisibility(true);
    setEmptyState(false);

    const fragment = document.createDocumentFragment();
    users.forEach((user) => {
        fragment.appendChild(createUserCard(user));
    });

    grid.appendChild(fragment);
    showFeedback(`Consulta carregada com ${users.length} usuario(s).`, "success");
}

async function loadUsersAndAccounts() {
    const token = getToken();
    if (!token) {
        return;
    }

    setLoadingState(true);
    setEmptyState(false);
    setGridVisibility(false);
    showFeedback("Carregando usuarios e contas...");

    try {
        const response = await fetch(USERS_ACCOUNTS_ENDPOINT, {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (response.status === 403) {
            window.location.href = "/home";
            return;
        }

        if (!response.ok) {
            setGridVisibility(false);
            setEmptyState(false);
            showFeedback("Nao foi possivel carregar os dados de gestao.", "error");
            return;
        }

        const payload = await response.json();
        renderUsers(payload.usuarios ?? []);
    } catch {
        setGridVisibility(false);
        setEmptyState(false);
        showFeedback("Erro de rede ao buscar usuarios e contas.", "error");
    } finally {
        setLoadingState(false);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    bindRenameModalEvents();

    const manager = await requireManagerUser();
    if (!manager) {
        return;
    }

    await loadUsersAndAccounts();
});
