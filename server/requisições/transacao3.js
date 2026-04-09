(function () {
  const params = new URLSearchParams(window.location.search);

  const valor = params.get('valor') || '—';
  const nome  = params.get('nome')  || '—';
  const banco = params.get('banco') || '—';

  const now = new Date();
  const data = now.toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });

  document.getElementById('detalhe-valor').textContent = 'R$ ' + valor;
  document.getElementById('detalhe-nome').textContent  = nome;
  document.getElementById('detalhe-banco').textContent = banco;
  document.getElementById('detalhe-data').textContent  = data;
})();