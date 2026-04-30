function setupMobileSidebar() {
    const sidebar = document.getElementById("sidebar");
    const openBtn = document.getElementById("btn-menu");
    const closeBtn = document.getElementById("btn-close-menu");
    const overlay = document.getElementById("overlay");

    if (!sidebar || !openBtn || !closeBtn || !overlay) {
        return;
    }

    const open = () => {
        sidebar.classList.add("open");
        overlay.classList.add("show");
    };

    const close = () => {
        sidebar.classList.remove("open");
        overlay.classList.remove("show");
    };

    openBtn.addEventListener("click", open);
    closeBtn.addEventListener("click", close);
    overlay.addEventListener("click", close);
}

document.addEventListener("DOMContentLoaded", setupMobileSidebar);
