const contacts = [
  { name: 'Gérsio Caminhoes',  initials: 'GO', bank: 'Nubank',    cpf: '123.456.789-09', phone: '(41) 99801-2345' },
  { name: 'Amanda Ferreira',   initials: 'AF', bank: 'Bradesco',  cpf: '987.654.321-00', phone: '(11) 98765-4321' },
  { name: 'Lucas Mendes',      initials: 'LM', bank: 'Itaú',      cpf: '321.654.987-01', phone: '(21) 99234-5678' },
  { name: 'Patricia Sousa',    initials: 'PS', bank: 'Santander', cpf: '741.852.963-02', phone: '(31) 98111-2233' },
  { name: 'Rafael Costa',      initials: 'RC', bank: 'C6 Bank',   cnpj: '12.345.678/0001-90', phone: '(85) 98800-9988' },
  { name: 'Juliana Lima',      initials: 'JL', bank: 'Inter',     cpf: '159.753.486-03', phone: '(71) 99300-4455' },
  { name: 'Bruno Alves',       initials: 'BA', bank: 'BB',        cnpj: '98.765.432/0001-10', phone: '(62) 98700-3322' },
  { name: 'Camila Rocha',      initials: 'CR', bank: 'Nubank',    cpf: '258.369.147-04', phone: '(51) 99900-7788' },
  { name: 'Diego Martins',     initials: 'DM', bank: 'Sicredi',   cpf: '963.258.741-05', phone: '(48) 98600-6644' },
];

const REGEX_FULL = {
  cpf:   /^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$/,
  cnpj:  /^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$/,
  phone: /^(\(?\d{2}\)?[\s\-]?)?(9\d{4}|\d{4})-?\d{4}$/,
};

function detectInputType(value) {
  const clean = value.trim();
  if (!clean) return 'text';
  if (clean.includes('/')) return 'cnpj';
  if (clean.includes('(') || clean.includes(')')) return 'phone';

  const digits = clean.replace(/\D/g, '');
  const onlyDigits = /^\d+$/.test(clean);
  const cpfChars   = /^[\d.\-]+$/.test(clean);
  const cnpjChars  = /^[\d.\-\/]+$/.test(clean);

  if (onlyDigits) {
    if (digits.length <= 11) return 'cpf';
    if (digits.length <= 14) return 'cnpj';
  }
  if (cpfChars && !clean.includes('/')) return 'cpf';
  if (cnpjChars) return 'cnpj';
  if (/^[\d\s\-]+$/.test(clean) && digits.length >= 8) return 'phone';
  return 'text';
}

function showInputFeedback(type, isComplete) {
  let el = document.getElementById('input-feedback');
  if (!el) {
    el = document.createElement('p');
    el.id = 'input-feedback';
    el.style.cssText = 'font-size:0.75rem; margin-top:-14px; padding-left:6px; min-height:18px; transition: color 0.2s;';
    document.querySelector('.search-wrapper').after(el);
  }
  const map = {
    cpf:   isComplete ? '✔ CPF válido'      : '· Buscando por CPF…',
    cnpj:  isComplete ? '✔ CNPJ válido'     : '· Buscando por CNPJ…',
    phone: isComplete ? '✔ Telefone válido' : '· Buscando por telefone…',
    text:  '',
  };
  el.textContent = map[type] || '';
  el.style.color = isComplete ? '#2eb8b8' : '#8abcbc';
}

function filterContacts(filter, type) {
  if (!filter) return contacts;
  const cleanDigits = filter.replace(/\D/g, '');
  const cleanLower  = filter.toLowerCase();
  return contacts.filter(c => {
    if (type === 'cpf')   return c.cpf   && c.cpf.replace(/\D/g, '').includes(cleanDigits);
    if (type === 'cnpj')  return c.cnpj  && c.cnpj.replace(/\D/g, '').includes(cleanDigits);
    if (type === 'phone') return c.phone && c.phone.replace(/\D/g, '').includes(cleanDigits);
    return c.name.toLowerCase().includes(cleanLower) || c.bank.toLowerCase().includes(cleanLower);
  });
}

function avatarSVG() {
  return `<svg class="contact-avatar-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
  </svg>`;
}

function checkSVG() {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
  </svg>`;
}

let selectedIndex = null;

function renderContacts(filter = '') {
  const grid = document.getElementById('contacts-grid');
  const type = detectInputType(filter);
  const clean = filter.replace(/\s/g, '');
  const isComplete = type !== 'text' && REGEX_FULL[type] && REGEX_FULL[type].test(clean);
  showInputFeedback(type, isComplete);

  const filtered = filterContacts(filter, type);

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="no-results">Nenhum contato encontrado</div>`;
    return;
  }

  grid.innerHTML = filtered.map(c => {
    const originalIndex = contacts.indexOf(c);
    const isSelected = selectedIndex === originalIndex;
    const keyInfo = c.cnpj || c.cpf || c.phone;
    return `
      <div class="contact-card ${isSelected ? 'selected' : ''}" data-index="${originalIndex}">
        <div class="contact-check">${checkSVG()}</div>
        <div class="contact-initials">${avatarSVG()}</div>
        <span class="contact-name">${c.name}</span>
        <span class="contact-bank">${c.bank}</span>
        <span class="contact-key">${keyInfo}</span>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.contact-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.index);
      selectedIndex = selectedIndex === idx ? null : idx;
      renderContacts(document.getElementById('search-input').value);
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  // Lê o valor da URL e atualiza o título
  const params = new URLSearchParams(window.location.search);
  const valor = params.get('valor');
  if (valor) {
    const el = document.getElementById('valor-titulo');
    if (el) el.textContent = 'R$ ' + valor;
  }

  // Init
  renderContacts();

  document.getElementById('search-input').addEventListener('input', e => {
    renderContacts(e.target.value);
  });

  document.getElementById('continue-btn').addEventListener('click', () => {
    if (selectedIndex === null) {
      alert('Selecione um contato para continuar.');
      return;
    }
    const c = contacts[selectedIndex];
    const params = new URLSearchParams(window.location.search);
    const valor = params.get('valor') || '0,00';
    window.location.href = '/transacao3?valor=' + encodeURIComponent(valor)
      + '&nome=' + encodeURIComponent(c.name)
      + '&banco=' + encodeURIComponent(c.bank);
  });
});