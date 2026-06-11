# ⚛️ ReactIA

<div align="center">

![ReactIA](./Versão%201.0.0.png)

### Assistente Inteligente Especializado em React

Uma IA desenvolvida para ensinar, orientar e responder dúvidas exclusivamente sobre React e seu ecossistema, utilizando Flask, Ollama e memória persistente para manter contexto entre conversas.

</div>

---

# 📖 Sobre o Projeto

O **ReactIA** é um assistente virtual especializado em React criado para auxiliar estudantes e desenvolvedores durante seus estudos.

Diferente de chatbots genéricos, a ReactIA foi configurada para responder apenas assuntos relacionados ao ecossistema React, oferecendo explicações práticas, exemplos objetivos e um roadmap estruturado para evolução do aluno.

O projeto utiliza:

- Frontend em HTML, CSS e JavaScript
- Backend Python com Flask
- Integração com Ollama
- Persistência de memória local
- Histórico de conversas
- Roadmap de estudos integrado
- Interface moderna responsiva

---

# ✨ Funcionalidades

## 🤖 Assistente Especializado

A ReactIA responde dúvidas sobre:

- React
- JSX
- Componentes
- Props
- State
- Hooks
- React Router
- Formulários
- Context API
- Bibliotecas React
- Vite
- Next.js
- Testes
- Boas práticas

---

## 🧠 Memória Persistente

O sistema salva automaticamente:

- Conversas anteriores
- Histórico de sessões
- Contexto recente
- Preferências do usuário

Os dados são armazenados em:

```bash
memory_base.json
```

---

## 📚 Roadmap de Estudos

A IA possui um roteiro de aprendizado próprio:

### 1. Fundamentos

- Componentes
- JSX
- Props
- Eventos

### 2. Hooks

- useState
- useEffect
- useRef

### 3. Manipulação de Dados

- Inputs controlados
- Validação
- Renderização condicional

### 4. Navegação

- React Router
- Rotas dinâmicas
- Layouts

### 5. Qualidade

- Organização
- Acessibilidade
- Testes

### 6. Projeto Final

- Integração com APIs
- Deploy
- Revisão completa

---

# 🏗️ Arquitetura

```text
┌─────────────────┐
│     Frontend    │
│ HTML + CSS + JS │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Flask Backend   │
│   server.py     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Ollama      │
│ minimax-m2.5    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Memory Storage  │
│ memory_base.json│
└─────────────────┘
```

---

# 📂 Estrutura do Projeto

```bash
ReactIA/
│
├── __pycache__/
│
├── node_modules/
│
├── Versão 1.0.0.png
│
├── index.html
│
├── index.js
│
├── memory_base.json
│
├── package.json
│
├── package-lock.json
│
├── requirements.txt
│
├── roadmap.html
│
├── server.py
│
├── styles.css
│
├── theme.js
│
└── README.md
```

---

# 📁 Explicação dos Arquivos

## server.py

Responsável por:

- Inicializar o Flask
- Gerenciar sessões
- Persistir memória
- Comunicar com o Ollama
- Expor APIs REST

---

## memory_base.json

Banco de memória local.

Armazena:

- Conversas
- Histórico
- Contexto persistente

---

## index.html

Estrutura principal da aplicação.

Contém:

- Interface do chat
- Sidebar
- Histórico
- Roadmap
- Alternância de tema

---

## index.js

Responsável por:

- Enviar mensagens
- Consumir APIs
- Atualizar interface
- Gerenciar sessões

---

## styles.css

Sistema completo de estilização:

- Layout responsivo
- Dark mode
- Light mode
- Animações
- Componentes

---

## theme.js

Controla:

- Tema claro
- Tema escuro
- Persistência da escolha

---

## roadmap.html

Página dedicada ao roteiro de estudos React.

---

# 🛠 Tecnologias Utilizadas

## Backend

- Python
- Flask
- JSON Storage
- Ollama API

---

## Frontend

- HTML5
- CSS3
- JavaScript ES6+

---

# 📦 Bibliotecas Utilizadas

## Flask

Framework web utilizado para criar a API.

```python
from flask import Flask
```

Funções:

- Rotas
- APIs
- Respostas HTTP
- Arquivos estáticos

---

## Ollama

Motor responsável pela geração das respostas da IA.

Modelo utilizado:

```text
minimax-m2.5:cloud
```

---

## GSAP

Biblioteca de animações.

CDN:

```html
https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js
```

Utilizada para:

- Transições
- Animações de entrada
- Interações visuais

---

## Iconify

Biblioteca de ícones.

CDN:

```html
https://code.iconify.design
```

Utilizada para:

- Logo React
- Ícones customizados

---

## Lucide Icons

Biblioteca moderna de ícones.

CDN:

```html
https://unpkg.com/lucide
```

Utilizada para:

- Botões
- Navegação
- Interface

---

## Google Fonts

Fonte principal:

```text
Inter
```

---

# 🔌 Endpoints da API

## Chat

```http
POST /chat
```

Envia uma pergunta para a ReactIA.

---

## Histórico

```http
GET /conversations
```

Lista todas as conversas.

---

## Conversa

```http
GET /conversation
```

Obtém mensagens de uma conversa.

---

## Memória

```http
GET /memory
```

Consulta estado da memória.

---

## Limpar Memória

```http
POST /memory/clear
```

Remove memória de uma sessão.

---

## Excluir Conversa

```http
POST /conversation/delete
```

Remove uma conversa completa.

---

# 🚀 Instalação

## 1. Clonar repositório

```bash
git clone https://github.com/WebersonRodrigues7/ReactIA.git
```

---

## 2. Entrar na pasta

```bash
cd ReactIA
```

---

## 3. Instalar dependências Python

```bash
pip install -r requirements.txt
```

---

## 4. Instalar Ollama

Baixe:

https://ollama.com

---

## 5. Baixar o modelo

```bash
ollama pull minimax-m2.5:cloud
```

---

## 6. Iniciar Ollama

```bash
ollama serve
```

---

## 7. Executar projeto

```bash
python server.py
```

---

# 🌐 Acessando

Após iniciar:

```text
http://localhost:3001
```

---

# 🔐 Segurança

O backend adiciona automaticamente:

```http
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

Melhorando segurança e privacidade.

---

# 🎯 Objetivo

A ReactIA foi criada para ser uma mentora virtual focada exclusivamente em React, ajudando estudantes a aprender de forma estruturada, prática e progressiva.

---

# 🔮 Roadmap do Projeto

## Futuras melhorias

- Autenticação
- Banco de dados real
- Upload de arquivos
- Exportação de conversas
- Suporte a Markdown
- Highlight de código
- Streaming de respostas
- Dashboard administrativo
- PWA
- Deploy em nuvem

---

# 👨‍💻 Desenvolvido por

### Weberson Rodrigues

Projeto educacional focado em ensino de React utilizando IA local com Ollama.

---

# 📄 Licença

Este projeto está disponível para estudos, modificações e aprendizado.

MIT License.
