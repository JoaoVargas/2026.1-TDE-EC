async function verificarLogin() {
  const token = localStorage.getItem('token');

  if (!token) {
    window.location.href = '../pages/login.html';
    return null;
  }

  const res = await fetch('http://localhost:8000/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!res.ok) {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    window.location.href = '../pages/login.html';
    return null;
  }

  return await res.json();
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('usuario');
  window.location.href = '../pages/login.html';
}