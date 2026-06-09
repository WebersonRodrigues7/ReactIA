const chatForm = document.querySelector('[data-chat-form]');
const chatInput = document.querySelector('[data-chat-input]');
const chatMessages = document.querySelector('[data-chat-messages]');
const submitButton = document.querySelector('[data-submit-button]');
const memoryCount = document.querySelector('[data-memory-count]');
const API_URL = '/chat';
const SESSION_KEY = 'reactia-session-id';

const sessionId = getSessionId();
const welcomeMessage = `Oi! Eu sou a ReactIA. Sua base de memoria esta ligada, entao eu consigo manter melhor o contexto das nossas aulas de React.`;

function getSessionId() {
  const saved = localStorage.getItem(SESSION_KEY);

  if (saved) {
    return saved;
  }

  const next = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  localStorage.setItem(SESSION_KEY, next);
  return next;
}

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
  submitButton.querySelector('span').textContent = isLoading ? 'Pensando...' : 'Enviar';
}

function updateMemoryCount(count) {
  if (!memoryCount) {
    return;
  }

  const label = count === 1 ? 'mensagem salva' : 'mensagens salvas';
  memoryCount.textContent = `${count} ${label}`;
}

async function loadMemoryStatus() {
  try {
    const response = await fetch(`/memory?sessionId=${encodeURIComponent(sessionId)}`);
    const data = await response.json();

    if (response.ok) {
      updateMemoryCount(data.messages || 0);
    }
  } catch {
    updateMemoryCount(0);
  }
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
      body: JSON.stringify({ message, sessionId })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Falha ao enviar mensagem.');
    }

    pendingMessage.querySelector('p').textContent = data.answer;
    updateMemoryCount(data.memorySize || 0);
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

createMessage(welcomeMessage, 'assistant');
loadMemoryStatus();

window.addEventListener('load', () => {
  if (window.lucide) {
    window.lucide.createIcons({
      attrs: {
        'stroke-width': 1.8
      }
    });
  }
});
