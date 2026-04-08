const API_URL = 'http://localhost:3000/cadastro';
 
// ─── Regras de validação por campo ───────────────────────────────────────────
 
const regras = {
  nome: (v) => {
    if (!v) return 'Nome completo é obrigatório.';
    if (v.length < 3) return 'Nome deve ter pelo menos 3 caracteres.';
    if (!/^[a-zA-ZÀ-ÿ\s]+$/.test(v)) return 'Nome não pode conter números ou símbolos.';
    return null;
  },
  email: (v) => {
    if (!v) return 'E-mail é obrigatório.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return 'Informe um e-mail válido.';
    return null;
  },
  cpf: (v) => {
    const nums = v.replace(/\D/g, '');
    if (!nums) return 'CPF é obrigatório.';
    if (nums.length !== 11) return 'CPF deve ter 11 dígitos.';
    if (!validarCPF(nums)) return 'CPF inválido.';
    return null;
  },
  nascimento: (v) => {
    if (!v) return 'Data de nascimento é obrigatória.';
    const nascimento = new Date(v);
    const hoje = new Date();
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const m = hoje.getMonth() - nascimento.getMonth();
    if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) idade--;
    if (idade < 18) return 'Você deve ter pelo menos 18 anos.';
    if (idade > 120) return 'Data de nascimento inválida.';
    return null;
  },
  senha: (v) => {
    if (!v) return 'Senha é obrigatória.';
    if (v.length < 8) return 'Senha deve ter pelo menos 8 caracteres.';
    if (!/[A-Z]/.test(v)) return 'Senha deve conter pelo menos uma letra maiúscula.';
    if (!/[0-9]/.test(v)) return 'Senha deve conter pelo menos um número.';
    return null;
  },
  confirmar: (v) => {
    const senha = document.getElementById('senha').value;
    if (!v) return 'Confirmação de senha é obrigatória.';
    if (v !== senha) return 'As senhas não coincidem.';
    return null;
  },
  cep: (v) => {
    const nums = v.replace(/\D/g, '');
    if (!nums) return 'CEP é obrigatório.';
    if (nums.length !== 8) return 'CEP deve ter 8 dígitos.';
    return null;
  },
  logradouro: (v) => {
    if (!v) return 'Logradouro é obrigatório.';
    return null;
  },
  numero: (v) => {
    if (!v) return 'Número é obrigatório.';
    return null;
  },
  bairro: (v) => {
    if (!v) return 'Bairro é obrigatório.';
    return null;
  },
  cidade: (v) => {
    if (!v) return 'Cidade é obrigatória.';
    return null;
  },
  estado: (v) => {
    if (!v) return 'Estado é obrigatório.';
    if (v.length !== 2) return 'Use a sigla do estado (ex: SP).';
    return null;
  },
};
 
// ─── Validação de CPF (algoritmo oficial) ─────────────────────────────────────
 
function validarCPF(nums) {
  if (/^(\d)\1{10}$/.test(nums)) return false;
  let soma = 0;
  for (let i = 0; i < 9; i++) soma += parseInt(nums[i]) * (10 - i);
  let resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(nums[9])) return false;
  soma = 0;
  for (let i = 0; i < 10; i++) soma += parseInt(nums[i]) * (11 - i);
  resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  return resto === parseInt(nums[10]);
}
 
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
 
// ─── Máscaras ────────────────────────────────────────────────────────────────
 
document.getElementById('cpf').addEventListener('input', (e) => {
  let v = e.target.value.replace(/\D/g, '').slice(0, 11);
  v = v.replace(/(\d{3})(\d)/, '$1.$2');
  v = v.replace(/(\d{3})(\d)/, '$1.$2');
  v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  e.target.value = v;
});
 
document.getElementById('cep').addEventListener('input', (e) => {
  let v = e.target.value.replace(/\D/g, '').slice(0, 8);
  v = v.replace(/(\d{5})(\d)/, '$1-$2');
  e.target.value = v;
});
 
document.getElementById('estado').addEventListener('input', (e) => {
  e.target.value = e.target.value.toUpperCase().slice(0, 2);
});
 
// ─── Busca automática de endereço pelo CEP (ViaCEP) ──────────────────────────
 
document.getElementById('cep').addEventListener('blur', async () => {
  const nums = document.getElementById('cep').value.replace(/\D/g, '');
  if (nums.length !== 8) return;
 
  try {
    const res = await fetch(`https://viacep.com.br/ws/${nums}/json/`);
    const data = await res.json();
    if (!data.erro) {
      document.getElementById('logradouro').value = data.logradouro || '';
      document.getElementById('bairro').value = data.bairro || '';
      document.getElementById('cidade').value = data.localidade || '';
      document.getElementById('estado').value = data.uf || '';
      ['logradouro', 'bairro', 'cidade', 'estado'].forEach(validarCampo);
    }
  } catch (_) {}
});
 
// ─── Eventos de validação em tempo real ──────────────────────────────────────
 
Object.keys(regras).forEach((id) => {
  const input = document.getElementById(id);
  if (!input) return;
 
  input.addEventListener('blur', () => validarCampo(id));
 
  input.addEventListener('input', () => {
    if (input.classList.contains('input-erro') || input.classList.contains('input-ok')) {
      validarCampo(id);
    }
  });
 
  if (id === 'senha') {
    input.addEventListener('input', () => {
      const confirmar = document.getElementById('confirmar');
      if (confirmar.classList.contains('input-erro') || confirmar.classList.contains('input-ok')) {
        validarCampo('confirmar');
      }
    });
  }
});
 
// ─── Envio do formulário ──────────────────────────────────────────────────────
 
document.getElementById('btn-finalizar').addEventListener('click', async () => {
  const campos = Object.keys(regras);
  const validos = campos.map(validarCampo);
 
  if (validos.includes(false)) {
    mostrarFeedback('Corrija os erros antes de continuar.', 'erro');
    return;
  }
 
  const dados = {
    nome:       document.getElementById('nome').value.trim(),
    email:      document.getElementById('email').value.trim(),
    cpf:        document.getElementById('cpf').value.replace(/\D/g, ''),
    nascimento: document.getElementById('nascimento').value,
    senha:      document.getElementById('senha').value,
    endereco: {
      cep:        document.getElementById('cep').value.replace(/\D/g, ''),
      logradouro: document.getElementById('logradouro').value.trim(),
      numero:     document.getElementById('numero').value.trim(),
      bairro:     document.getElementById('bairro').value.trim(),
      cidade:     document.getElementById('cidade').value.trim(),
      estado:     document.getElementById('estado').value.trim(),
    }
  };
 
  const btn = document.getElementById('btn-finalizar');
  btn.disabled = true;
  btn.textContent = 'Enviando...';
 
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
 
    const resultado = await response.json();
 
    if (response.ok) {
      mostrarFeedback('Cadastro realizado com sucesso!', 'sucesso');
      // setTimeout(() => window.location.href = '../pages/login.html', 2000);
    } else {
      mostrarFeedback(resultado.message || resultado.error || 'Erro ao realizar cadastro.', 'erro');
    }
  } catch (error) {
    console.error('Erro na requisição:', error);
    mostrarFeedback('Não foi possível conectar ao servidor.', 'erro');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Finalizar Cadastro';
  }
});
 
// ─── Feedback global ─────────────────────────────────────────────────────────
 
function mostrarFeedback(texto, tipo) {
  const el = document.getElementById('mensagem');
  el.textContent = texto;
  el.className = 'mensagem ' + tipo;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 5000);
}