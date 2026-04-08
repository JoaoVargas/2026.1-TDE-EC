const API_URL = 'http://localhost:3000/login'; // add o localhost ainda

// ─── Regras de validação ──────────────────────────────────────────────────────

const regras = {
  cpf: (v) => {
    const nums = v.replace(/\D/g, '');
    if (!nums) return 'CPF é obrigatório.';
    if (nums.length !== 11) return 'CPF deve ter 11 dígitos.';
    return null;
  },
  senha: (v) => {
    if (!v) return 'Senha é obrigatória.';
    if (v.length < 8) return 'Senha deve ter pelo menos 8 caracteres.';
    return null;
  },
};

// ─── Exibe / limpa erro de um campo ──────────────────────────────────────────

function mostrarErro(id, mensagem) {
  const input = document.getElementById(id);
  const grupo = input.closest('.form-group');
  let span = grupo.querySelector('.erro-campo');

  if (!span) {
    span = document.createElement('span');
    span.className = 'erro-campo';
    grupo.appendChild(span);
  }

  if (mensagem) {
    span.textContent = mensagem;
    input.classList.add('input-erro');
    input.classList.remove('input-ok');
  } else {
    span.textContent = '';
    input.classList.remove('input-erro');
    input.classList.add('input-ok');
  }
}

function validarCampo(id) {
  const input = document.getElementById(id);
  const regra = regras[id];
  if (!regra) return true;
  const erro = regra(input.value.trim());
  mostrarErro(id, erro);
  return !erro;
}

// ─── Máscara CPF ─────────────────────────────────────────────────────────────

document.getElementById('cpf').addEventListener('input', (e) => {
  let v = e.target.value.replace(/\D/g, '').slice(0, 11);
  v = v.replace(/(\d{3})(\d)/, '$1.$2');
  v = v.replace(/(\d{3})(\d)/, '$1.$2');
  v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  e.target.value = v;
});

// ─── Validação em tempo real ──────────────────────────────────────────────────

Object.keys(regras).forEach((id) => {
  const input = document.getElementById(id);
  if (!input) return;

  input.addEventListener('blur', () => validarCampo(id));

  input.addEventListener('input', () => {
    if (input.classList.contains('input-erro') || input.classList.contains('input-ok')) {
      validarCampo(id);
    }
  });
});

// ─── Envio ────────────────────────────────────────────────────────────────────

document.getElementById('btn-login').addEventListener('click', async () => {
  const validos = Object.keys(regras).map(validarCampo);

  if (validos.includes(false)) return;

  const dados = {
    cpf:   document.getElementById('cpf').value.replace(/\D/g, ''),
    senha: document.getElementById('senha').value,
  };

  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Entrando...';

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });

    const resultado = await response.json();

    if (response.ok) {
      mostrarFeedback('Login realizado com sucesso!', 'sucesso');
      // setTimeout(() => window.location.href = '../pages/dashboard.html', 1500);
    } else {
      mostrarFeedback(resultado.message || 'CPF ou senha incorretos.', 'erro');
    }
  } catch (error) {
    console.error('Erro na requisição:', error);
    mostrarFeedback('Não foi possível conectar ao servidor.', 'erro');
  } finally {
    btn.disabled = false;
    btn.textContent = 'LOGIN';
  }
});

// ─── Feedback global ──────────────────────────────────────────────────────────

function mostrarFeedback(texto, tipo) {
  const el = document.getElementById('mensagem');
  el.textContent = texto;
  el.className = 'mensagem ' + tipo;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 5000);
}