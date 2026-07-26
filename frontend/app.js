const API_URL = localStorage.getItem('shiksha_api_url') || 'http://127.0.0.1:8000/api';
const dialog = document.querySelector('#auth-dialog');
const template = document.querySelector('#auth-template');

function openAuth(mode) {
  const fragment = template.content.cloneNode(true);
  const content = fragment.querySelector('.auth-card');
  const register = mode === 'register';
  content.querySelector('h2').textContent = register ? 'Start your learning journey' : 'Welcome back';
  content.querySelector('.muted').textContent = register ? 'Create your free account to get started.' : 'Log in to continue where you left off.';
  content.querySelector('.name-field').hidden = !register;
  content.querySelector('.submit').textContent = register ? 'Create account' : 'Log in';
  content.querySelector('.switch-auth').innerHTML = register ? 'Already learning? <button type="button">Log in</button>' : 'New to Shiksha AI? <button type="button">Create an account</button>';
  content.querySelector('.switch-auth button').onclick = () => openAuth(register ? 'login' : 'register');
  content.querySelector('#auth-form').onsubmit = (event) => submitAuth(event, register);
  document.querySelector('#auth-content').replaceChildren(fragment);
  dialog.showModal();
}

async function submitAuth(event, register) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector('button[type="submit"]');
  const error = form.querySelector('.form-error');
  const values = Object.fromEntries(new FormData(form));
  if (!register) delete values.name;
  button.disabled = true; button.textContent = 'Please wait…'; error.textContent = '';
  try {
    const response = await fetch(`${API_URL}/auth/${register ? 'register' : 'login'}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Something went wrong.');
    localStorage.setItem('shiksha_token', data.access_token);
    localStorage.setItem('shiksha_user', JSON.stringify(data.user));
    window.location.href = 'dashboard.html';
  } catch (err) { error.textContent = err.message; button.disabled = false; button.textContent = register ? 'Create account' : 'Log in'; }
}

document.querySelectorAll('[data-open-auth]').forEach(button => button.onclick = () => openAuth(button.dataset.openAuth));
dialog.querySelector('.close').onclick = () => dialog.close();

