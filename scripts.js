// Sample scripts for index.html

function showGreeting() {
  const greeting = document.getElementById('greeting');
  if (greeting) {
    greeting.textContent = 'Welcome to the Hello World page!';
  }
}

function toggleTheme() {
  document.body.classList.toggle('dark-theme');
}

function updateClock() {
  const clock = document.getElementById('clock');
  if (!clock) return;
  const now = new Date();
  clock.textContent = now.toLocaleTimeString();
}

function handleFormSubmit(event) {
  event.preventDefault();
  const nameInput = document.getElementById('name');
  const output = document.getElementById('name-output');
  if (nameInput && output) {
    output.textContent = `Hello, ${nameInput.value || 'guest'}!`;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  showGreeting();
  updateClock();
  setInterval(updateClock, 1000);

  const themeButton = document.getElementById('theme-button');
  if (themeButton) {
    themeButton.addEventListener('click', toggleTheme);
  }

  const form = document.getElementById('hello-form');
  if (form) {
    form.addEventListener('submit', handleFormSubmit);
  }
});