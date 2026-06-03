import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import ollama from 'ollama';

const PORT = process.env.PORT || 3001;
const MODEL = 'minimax-m2.5:cloud';
const ROOT = fileURLToPath(new URL('.', import.meta.url));

const SYSTEM_PROMPT = `
Voce e a ReactIA, uma IA especialista em desenvolvimento React.
Ajude somente com React e seu ecossistema: componentes, hooks, estado,
props, roteamento, formularios, bibliotecas React, Vite, Next.js, testes,
estilizacao e boas praticas de frontend React.

Regras:
- Responda em pt-BR.
- Use exemplos práticos e curtos quando ajudar.
- Se o usuario pedir algo fora de React ou bibliotecas/hooks React,
  explique com gentileza que voce so pode ajudar nesse tema.
- Nao mencione nem use outro provedor/modelo de IA. O modelo permitido e ${MODEL}.
`.trim();

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function sendJson(res, status, data) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store'
  });
  res.end(JSON.stringify(data));
}

async function readRequestBody(req) {
  const chunks = [];

  for await (const chunk of req) {
    chunks.push(chunk);

    if (Buffer.concat(chunks).length > 32_000) {
      throw new Error('Mensagem muito grande.');
    }
  }

  return JSON.parse(Buffer.concat(chunks).toString('utf-8') || '{}');
}

async function handleChat(req, res) {
  try {
    const body = await readRequestBody(req);
    const userMessage = String(body.message || '').trim();

    if (!userMessage) {
      sendJson(res, 400, { error: 'Escreva uma pergunta sobre React.' });
      return;
    }

    const response = await ollama.chat({
      model: MODEL,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userMessage }
      ],
      options: {
        temperature: 0.35
      }
    });

    sendJson(res, 200, {
      answer: response.message?.content || 'Nao consegui gerar uma resposta agora.'
    });
  } catch (error) {
    console.error('Erro em /chat:', error);
    sendJson(res, 500, {
      error: 'Nao consegui falar com o Ollama. Confira se o Ollama esta aberto e se o modelo minimax-m2.5:cloud esta disponivel.'
    });
  }
}

async function serveStatic(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const requestedPath = url.pathname === '/' ? '/index.html' : url.pathname;
  const safePath = normalize(requestedPath).replace(/^(\.\.[/\\])+/, '');
  const filePath = join(ROOT, safePath);

  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  try {
    const file = await readFile(filePath);
    const type = MIME_TYPES[extname(filePath)] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': type,
      'Cache-Control': 'no-store'
    });
    res.end(file);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Arquivo nao encontrado.');
  }
}

const server = createServer(async (req, res) => {
  if (req.method === 'POST' && req.url === '/chat') {
    await handleChat(req, res);
    return;
  }

  if (req.method === 'GET' || req.method === 'HEAD') {
    await serveStatic(req, res);
    return;
  }

  res.writeHead(405, { Allow: 'GET, HEAD, POST' });
  res.end();
});

server.listen(PORT, () => {
  console.log(`ReactIA rodando em http://localhost:${PORT}`);
  console.log(`Modelo Ollama: ${MODEL}`);
});
