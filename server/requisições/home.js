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
  console.log("Token:", localStorage.getItem("token"));
  console.log("Usuario:", localStorage.getItem("usuario"));

  // 🔽 AGORA SIM, DEPOIS QUE O DOM EXISTE

  const sidebar  = document.querySelector(".sidebar");
  const btnMenu  = document.getElementById("btn-menu");
  const overlay  = document.getElementById("overlay");
  const transacao = document.getElementById('transacao');
  const investimento = document.getElementById('investimento');
  btnMenu.addEventListener("click", function () {
    sidebar.classList.add("aberta");
    overlay.classList.add("ativo");
  });

  overlay.addEventListener("click", function () {
    sidebar.classList.remove("aberta");
    overlay.classList.remove("ativo");
  });

  transacao.addEventListener("click", function (e) {
    e.preventDefault();
    console.log("indo para transacao");
    window.location.href = '/transacao';
  });
  investimento.addEventListener("click", function (e) {
      e.preventDefault();
      console.log("indo para investimento");
      window.location.href = '/investimentos';
    });
});