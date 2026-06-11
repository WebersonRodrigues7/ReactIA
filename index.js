const chatForm = document.querySelector('[data-chat-form]');
const chatInput = document.querySelector('[data-chat-input]');
const chatMessages = document.querySelector('[data-chat-messages]');
const submitButton = document.querySelector('[data-submit-button]');
const memoryCount = document.querySelector('[data-memory-count]');
const conversationList = document.querySelector('[data-conversation-list]');
const newChatButton = document.querySelector('[data-new-chat]');
const chatTitle = document.querySelector('[data-chat-title]');
const openPanelButton = document.querySelector('[data-open-panel]');
const closePanelButton = document.querySelector('[data-close-panel]');
const drawerBackdrop = document.querySelector('[data-drawer-backdrop]');
const themeToggle = document.querySelector('[data-theme-toggle]');

const API_URL = '/chat';
const SESSION_KEY = 'reactia-session-id';
const THEME_KEY = 'reactia-theme';
const studyPrompts = [
  'Com o que posso te ajudar hoje?',
  'Qual parte do React voce quer entender melhor hoje?',
  'Vamos transformar sua duvida em pratica?',
  'Quer revisar hooks, componentes ou estado?',
  'Me diga onde voce travou e eu te guio passo a passo.',
  'Pronto para estudar React com exemplos curtos?'
];

let sessionId = getSessionId();
let conversations = [];
let emptyPrompt = pickStudyPrompt();
let hasPlayedIntro = false;

function makeSessionId() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
}

function getSessionId() {
  const saved = localStorage.getItem(SESSION_KEY);

  if (saved) {
    return saved;
  }

  const next = makeSessionId();
  localStorage.setItem(SESSION_KEY, next);
  return next;
}

function setSessionId(nextSessionId) {
  sessionId = nextSessionId;
  localStorage.setItem(SESSION_KEY, nextSessionId);
}

function clearMessages() {
  chatMessages.replaceChildren();
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons({
      attrs: {
        'stroke-width': 1.8
      }
    });
  }

  if (window.Iconify) {
    window.Iconify.scan();
  }
}

function animateIntro() {
  if (!window.gsap || hasPlayedIntro) {
    return;
  }

  hasPlayedIntro = true;

  const timeline = window.gsap.timeline({ defaults: { ease: 'power3.out' } });
  timeline
    .from('.chat__header', { y: -24, opacity: 0, duration: 0.65 })
    .from('.top-brand__mark', { y: -18, scale: 0.35, rotation: -45, opacity: 0, duration: 0.7 }, '-=0.28')
    .from('.top-brand h1, .top-brand p', { y: 12, opacity: 0, stagger: 0.08, duration: 0.45 }, '-=0.35')
    .from('.empty-state__logo', { y: 34, scale: 0.55, rotation: 90, opacity: 0, duration: 0.9 }, '-=0.15')
    .from('.empty-state h2', { y: 18, opacity: 0, filter: 'blur(10px)', duration: 0.72 }, '-=0.35')
    .from('.empty-state p', { y: 14, opacity: 0, duration: 0.55 }, '-=0.3')
    .from('.composer', { y: 36, scale: 0.96, opacity: 0, duration: 0.58 }, '-=0.2');
}

function animateMessage(message) {
  if (!window.gsap) {
    return;
  }

  window.gsap.from(message, {
    y: 18,
    opacity: 0,
    scale: 0.985,
    duration: 0.42,
    ease: 'power3.out'
  });
}

function animateChatOpen() {
  if (document.body.dataset.chatStarted === 'true') {
    return;
  }

  document.body.dataset.chatStarted = 'true';

  if (!window.gsap) {
    return;
  }

  window.gsap.timeline({ defaults: { ease: 'power3.inOut' } })
    .to('.empty-state', {
      y: -30,
      opacity: 0,
      filter: 'blur(12px)',
      duration: 0.34
    })
    .fromTo('.composer', {
      y: -120,
      scale: 0.92
    }, {
      y: 0,
      scale: 1,
      duration: 0.55
    }, '-=0.1');
}

function setChatStarted(isStarted) {
  document.body.dataset.chatStarted = isStarted ? 'true' : 'false';
}

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function pickStudyPrompt() {
  return studyPrompts[Math.floor(Math.random() * studyPrompts.length)];
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
  animateMessage(article);

  return article;
}

function renderEmptyConversation() {
  clearMessages();

  const emptyState = document.createElement('section');
  emptyState.className = 'empty-state';

  const logo = document.createElement('span');
  logo.className = 'empty-state__logo iconify';
  logo.dataset.icon = 'logos:react';
  logo.dataset.width = '78';
  logo.dataset.height = '78';

  const title = document.createElement('h2');
  title.textContent = emptyPrompt;

  const subtitle = document.createElement('p');
  subtitle.textContent = 'Pergunte sobre componentes, hooks, props, rotas ou qualquer etapa do seu estudo em React.';

  emptyState.append(logo, title, subtitle);
  chatMessages.append(emptyState);
  refreshIcons();
  requestAnimationFrame(animateIntro);
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  chatInput.disabled = isLoading;
  submitButton.querySelector('span').textContent = isLoading ? 'Pensando...' : 'Enviar';
}

function pulseControl(selector) {
  if (!window.gsap) {
    return;
  }

  window.gsap.fromTo(selector, {
    scale: 0.92
  }, {
    scale: 1,
    duration: 0.35,
    ease: 'back.out(2.4)'
  });
}

function updateMemoryCount(count) {
  if (!memoryCount) {
    return;
  }

  const label = count === 1 ? 'mensagem' : 'mensagens';
  memoryCount.textContent = `${count} ${label}`;
}

function renderConversationList() {
  conversationList.replaceChildren();

  if (!conversations.length) {
    const empty = document.createElement('p');
    empty.className = 'conversation-empty';
    empty.textContent = 'Suas conversas salvas vao aparecer aqui.';
    conversationList.append(empty);
    return;
  }

  conversations.forEach((conversation) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'conversation-item';
    button.dataset.active = conversation.id === sessionId ? 'true' : 'false';
    button.addEventListener('click', () => {
      loadConversation(conversation.id);
      closePanel();
    });

    const title = document.createElement('strong');
    title.textContent = conversation.title;

    const meta = document.createElement('span');
    const label = conversation.messages === 1 ? 'mensagem' : 'mensagens';
    meta.textContent = `${conversation.messages} ${label}`;

    button.append(title, meta);
    conversationList.append(button);
  });
}

function updateConversationTitle(title) {
  chatTitle.textContent = title || 'Nova conversa';
}

async function loadConversations() {
  try {
    const response = await fetch('/conversations');
    const data = await response.json();

    if (!response.ok) {
      throw new Error('Nao foi possivel carregar o historico.');
    }

    conversations = data.conversations || [];
    renderConversationList();
  } catch {
    conversations = [];
    renderConversationList();
  }
}

async function loadConversation(nextSessionId = sessionId) {
  setSessionId(nextSessionId);
  setLoading(true);

  try {
    const response = await fetch(`/conversation?sessionId=${encodeURIComponent(sessionId)}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error('Nao foi possivel abrir esta conversa.');
    }

    clearMessages();

    if (data.items && data.items.length) {
      setChatStarted(true);
      data.items.forEach((message) => createMessage(message.content, message.role));
    } else {
      setChatStarted(false);
      renderEmptyConversation();
    }

    updateConversationTitle(data.title);
    updateMemoryCount(data.messages || 0);
  } catch (error) {
    clearMessages();
    createMessage(error.message, 'assistant').classList.add('message--error');
  } finally {
    setLoading(false);
    await loadConversations();
    chatInput.focus();
  }
}

function startNewConversation() {
  setSessionId(makeSessionId());
  emptyPrompt = pickStudyPrompt();
  setChatStarted(false);
  updateConversationTitle('Nova conversa');
  updateMemoryCount(0);
  renderEmptyConversation();
  renderConversationList();
  closePanel();
  chatInput.focus();
}

async function askReactIA(message) {
  setLoading(true);

  if (chatMessages.querySelector('.empty-state')) {
    animateChatOpen();
    await wait(window.gsap ? 320 : 0);
    clearMessages();
  } else {
    setChatStarted(true);
  }

  createMessage(message, 'user');
  const pendingMessage = createMessage('Pensando em uma resposta focada em React...', 'assistant');

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
    await loadConversations();
    const active = conversations.find((conversation) => conversation.id === sessionId);
    updateConversationTitle(active ? active.title : 'Conversa React');
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

chatInput.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter' || event.shiftKey) {
    return;
  }

  event.preventDefault();
  chatForm.requestSubmit();
});

function openPanel() {
  document.body.dataset.panelOpen = 'true';

  if (window.gsap) {
    window.gsap.fromTo('.panel', {
      x: -28,
      opacity: 0.72
    }, {
      x: 0,
      opacity: 1,
      duration: 0.42,
      ease: 'power3.out',
      clearProps: 'transform,opacity'
    });
    window.gsap.from('.conversation-item, .new-chat-button, .roadmap-link', {
      x: -14,
      opacity: 0,
      stagger: 0.035,
      duration: 0.34,
      ease: 'power2.out'
    });
  }
}

function closePanel() {
  document.body.dataset.panelOpen = 'false';
}

function applyTheme(theme) {
  const nextTheme = theme === 'dark' ? 'dark' : 'light';
  document.body.dataset.theme = nextTheme;
  localStorage.setItem(THEME_KEY, nextTheme);

  if (themeToggle) {
    themeToggle.innerHTML = `<i data-lucide="${nextTheme === 'dark' ? 'sun' : 'moon'}"></i>`;
    themeToggle.setAttribute('aria-label', nextTheme === 'dark' ? 'Alternar para modo claro' : 'Alternar para modo escuro');
    refreshIcons();
  }
}

openPanelButton.addEventListener('click', openPanel);
closePanelButton.addEventListener('click', closePanel);
drawerBackdrop.addEventListener('click', closePanel);

themeToggle.addEventListener('click', () => {
  applyTheme(document.body.dataset.theme === 'dark' ? 'light' : 'dark');
  pulseControl('[data-theme-toggle]');
});

newChatButton.addEventListener('click', startNewConversation);

applyTheme(localStorage.getItem(THEME_KEY) || 'light');
loadConversations().then(() => loadConversation(sessionId));

window.addEventListener('load', () => {
  refreshIcons();
});
