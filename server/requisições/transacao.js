const display = document.getElementById('display');
const delBtn = document.getElementById('del-btn');
const continueBtn = document.getElementById('continue-btn');

let digits = ''; // stores raw digits string e.g. "1234" = R$ 12,34

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

continueBtn.addEventListener('click', () => {
  if (digits === '') return;
  const value = display.textContent.replace('R$: ', '');
  window.location.href = 'transacao2.html?valor=' + encodeURIComponent(value);
});