import { requireAuthenticatedUser, logout } from "/static/js/components/auth-token-guard.js";

function isManagerUser(user) {
    const role = String(user?.type || "").trim().toLowerCase();
    return role === "manager";
}

function getCachedUser() {
    const raw = localStorage.getItem("user");
    if (!raw) {
        return null;
    }

    try {
        return JSON.parse(raw);
    } catch {
        localStorage.removeItem("user");
        return null;
    }
}

function getInitials(name) {
    if (!name) {
        return "U";
    }

    return (
        name
            .split(" ")
            .filter(Boolean)
            .slice(0, 2)
            .map((part) => part[0].toUpperCase())
            .join("") || "U"
    );
}

function setupMobileSidebar() {
    const sidebar = document.getElementById("sidebar");
    const openBtn = document.getElementById("btn-menu");
    const closeBtn = document.getElementById("btn-close-menu");
    const overlay = document.getElementById("overlay");

    if (!sidebar || !openBtn || !closeBtn || !overlay) {
        return;
    }

    const openSidebar = () => {
        sidebar.classList.add("open");
        overlay.classList.add("show");
    };

    const closeSidebar = () => {
        sidebar.classList.remove("open");
        overlay.classList.remove("show");
    };

    openBtn.addEventListener("click", openSidebar);
    closeBtn.addEventListener("click", closeSidebar);
    overlay.addEventListener("click", closeSidebar);
}

function hydrateUser(user) {
    const userName = user?.name || "Usuario";
    const userEmail = user?.email || "conta@betabank.local";

    const welcomeTitle = document.getElementById("welcome-title");
    const profileName = document.getElementById("profile-name");
    const profileEmail = document.getElementById("profile-email");
    const avatar = document.getElementById("user-avatar");

    if (welcomeTitle) {
        welcomeTitle.textContent = `Ola, ${userName}`;
    }
    if (profileName) {
        profileName.textContent = userName;
    }
    if (profileEmail) {
        profileEmail.textContent = userEmail;
    }
    if (avatar) {
        avatar.textContent = getInitials(userName);
    }
}

function applyRoleAwareNavigation(user) {
    const managerLink = document.getElementById("manager-nav-link");
    if (!managerLink) {
        return;
    }

    if (isManagerUser(user)) {
        managerLink.classList.add("is-visible");
        return;
    }

    managerLink.classList.remove("is-visible");
}

document.addEventListener("DOMContentLoaded", async () => {
    setupMobileSidebar();

    const logoutBtn = document.getElementById("btn-logout");
    logoutBtn?.addEventListener("click", logout);

    const cachedUser = getCachedUser();
    if (cachedUser) {
        hydrateUser(cachedUser);
        applyRoleAwareNavigation(cachedUser);
    }

    const user = await requireAuthenticatedUser();
    if (!user) {
        return;
    }

    hydrateUser(user);
    applyRoleAwareNavigation(user);
});
