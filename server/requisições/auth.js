async function verificarLogin() {
  const token = localStorage.getItem('token');

  if (!token) {
    window.location.href = '/login';
    return null;
  }

  const res = await fetch('http://localhost:8000/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = '../template/login.html';
    return null;
  }

  return await res.json();
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('usuario');
  window.location.href = '../template/login.html';
}