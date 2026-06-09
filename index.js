const chatForm = document.querySelector('[data-chat-form]');
const chatInput = document.querySelector('[data-chat-input]');
const chatMessages = document.querySelector('[data-chat-messages]');
const submitButton = document.querySelector('[data-submit-button]');
const quickPrompts = document.querySelectorAll('[data-prompt]');
const API_URL = '/chat';

const welcomeMessage = `Oi! Eu sou a ReactIA. Me pergunte sobre componentes, hooks, estado, props, bibliotecas React, testes, rotas ou qualquer detalhe do ecossistema React.`;

function createMessage(content, role) {
  const article = document.createElement('article');
  article.className = `message message--${role}`;

  const label = document.createElement('span');
  label.className = 'message__label';
  label.textContent = role === 'user' ? 'Voce' : 'ReactIA';

  const text = document.createElement('p');
  text.textContent = content;

  article.append(label, text);
  chatMessages.append(article);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return article;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  chatInput.disabled = isLoading;
  submitButton.textContent = isLoading ? 'Pensando...' : 'Enviar';
}

async function askReactIA(message) {
  createMessage(message, 'user');
  const pendingMessage = createMessage('Pensando em uma resposta focada em React...', 'assistant');

  setLoading(true);

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Falha ao enviar mensagem.');
    }

    pendingMessage.querySelector('p').textContent = data.answer;
  } catch (error) {
    pendingMessage.querySelector('p').textContent = error.message;
    pendingMessage.classList.add('message--error');
  } finally {
    setLoading(false);
    chatInput.focus();
  }
}

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const message = chatInput.value.trim();

  if (!message) {
    chatInput.focus();
    return;
  }

  chatInput.value = '';
  askReactIA(message);
});

quickPrompts.forEach((button) => {
  button.addEventListener('click', () => {
    chatInput.value = button.dataset.prompt;
    chatInput.focus();
  });
});

createMessage(welcomeMessage, 'assistant');
