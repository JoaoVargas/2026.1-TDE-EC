// ─────────────────────────────────────
// SIDEBAR DESLIZANTE (mobile)
// ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = '/login';
    return;
  }

  const res = await fetch('http://localhost:8000/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = '/login';
    return;
  }

  const usuario = await res.json();
  console.log("Logado como:", usuario.nome);
  // use os dados do usuário aqui se precisar
});

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