document.addEventListener("DOMContentLoaded", async () => {
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
  const display = document.getElementById('display');
  const delBtn = document.getElementById('del-btn');
  const continueBtn = document.getElementById('continue-btn');

  let digits = '';

  function updateDisplay() {
    if (digits === '') {
      display.textContent = 'R$: 0,00';
      return;
    }
    const padded = digits.padStart(3, '0');
    const intPart = padded.slice(0, -2).replace(/^0+(?=\d)/, '') || '0';
    const decPart = padded.slice(-2);
    display.textContent = `R$: ${intPart},${decPart}`;
  }

  function bump() {
    display.classList.remove('bump');
    void display.offsetWidth;
    display.classList.add('bump');
    display.addEventListener('animationend', () => display.classList.remove('bump'), { once: true });
  }

  document.querySelectorAll('.key[data-val]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (digits.length >= 10) return;
      digits += btn.dataset.val;
      updateDisplay();
      bump();
    });
  });

  delBtn.addEventListener('click', () => {
    if (digits.length === 0) return;
    digits = digits.slice(0, -1);
    updateDisplay();
  });

  console.log("botao:", continueBtn);

  continueBtn.addEventListener('click', () => {
    console.log("clicou");
    
    const value = display.textContent.replace('R$: ', '').trim();
    console.log("valor:"+value);
    window.location.href = '/transacao2?valor=' + encodeURIComponent(value);
  });

});