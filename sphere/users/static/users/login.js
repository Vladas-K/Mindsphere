const password = document.getElementById('id_password');
const toggle = document.querySelector('.password-toggle');
if (password && toggle) {
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const visible = password.type === 'password';
    password.type = visible ? 'text' : 'password';
    toggle.textContent = visible ? 'Скрыть' : 'Показать';
    toggle.setAttribute('aria-pressed', String(visible));
  });
}
