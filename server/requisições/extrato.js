// ─────────────────────────────────────
// FILTROS DO EXTRATO
// ─────────────────────────────────────

const filtros    = document.querySelectorAll(".filtro");
const transacoes = document.querySelectorAll(".transacao");

filtros.forEach(function(btn) {
  btn.addEventListener("click", function() {

    // Remove o ativo de todos e coloca no clicado
    filtros.forEach(f => f.classList.remove("ativo"));
    btn.classList.add("ativo");

    const tipo = btn.textContent;

    transacoes.forEach(function(t) {
      const isEntrada = t.querySelector(".transacao-valor--entrada");

      if (tipo === "Tudo")          t.style.display = "";
      else if (tipo === "Entradas") t.style.display = isEntrada ? "" : "none";
      else if (tipo === "Saídas")   t.style.display = isEntrada ? "none" : "";
      else if (tipo === "Este mês") t.style.display = ""; // futuramente filtra por data
    });
  });
});