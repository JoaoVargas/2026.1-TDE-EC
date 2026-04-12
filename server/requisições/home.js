// ─────────────────────────────────────
// SIDEBAR DESLIZANTE (mobile)
// ─────────────────────────────────────

const sidebar  = document.querySelector(".sidebar");
const btnMenu  = document.getElementById("btn-menu");
const overlay  = document.getElementById("overlay");

// Abre a sidebar
btnMenu.addEventListener("click", function () {
  sidebar.classList.add("aberta");
  overlay.classList.add("ativo");
});

// Fecha ao clicar no overlay
overlay.addEventListener("click", function () {
  sidebar.classList.remove("aberta");
  overlay.classList.remove("ativo");
});