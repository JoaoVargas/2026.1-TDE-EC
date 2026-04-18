import { requireAuthenticatedUser, logout } from "/static/js/components/auth-token-guard.js";

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
    const userName = user?.nome || "Usuario";
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

document.addEventListener("DOMContentLoaded", async () => {
    const user = await requireAuthenticatedUser();
    if (!user) {
        return;
    }

    hydrateUser(user);
    setupMobileSidebar();

    const logoutBtn = document.getElementById("btn-logout");
    logoutBtn?.addEventListener("click", logout);
});
