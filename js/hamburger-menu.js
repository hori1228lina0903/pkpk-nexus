document.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('menu-button');
  const menu = document.getElementById('menu');

  button.addEventListener('click', () => {
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    menu.classList.toggle('active');
  });
});