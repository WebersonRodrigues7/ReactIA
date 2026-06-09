import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
import json

from flask import Flask, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "3001"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = "minimax-m2.5:cloud"
MAX_MEMORY_MESSAGES = 14
CONVERSATION_MEMORY = {}

SYSTEM_PROMPT = f"""
Voce e a ReactIA, uma IA especialista em desenvolvimento React.
Ajude somente com React e seu ecossistema: componentes, hooks, estado,
props, roteamento, formularios, bibliotecas React, Vite, Next.js, testes,
estilizacao e boas praticas de frontend React.

Regras:
- Responda em pt-BR.
- Use exemplos praticos e curtos quando ajudar.
- Quando o usuario pedir orientacao de estudo, siga este roadmap:
  1. Base do React: componentes, JSX, props, estado local e eventos.
  2. Hooks essenciais: useState, useEffect, useRef e composicao.
  3. Formularios e dados: inputs controlados, validacao, listas e condicionais.
  4. Navegacao: React Router, paginas, parametros e layouts.
  5. Qualidade: organizacao, acessibilidade, testes e boas praticas.
  6. Projeto final: aplicacao completa com API, revisao e publicacao.
- Sugira o proximo passo do roadmap quando isso for util para o aluno.
- Se o usuario pedir algo fora de React ou bibliotecas/hooks React,
  explique com gentileza que voce so pode ajudar nesse tema.
- Nao mencione nem use outro provedor/modelo de IA. O modelo permitido e {MODEL}.
""".strip()

app = Flask(__name__, static_folder=None)


def normalize_session_id(value):
    session_id = str(value or "default").strip()
    safe = "".join(char for char in session_id if char.isalnum() or char in "-_")
    return safe[:80] or "default"


def get_memory(session_id):
    return CONVERSATION_MEMORY.setdefault(session_id, [])


def remember(session_id, role, content):
    memory = get_memory(session_id)
    memory.append({"role": role, "content": content})
    del memory[:-MAX_MEMORY_MESSAGES]


def ask_ollama(session_id, user_message):
    memory = get_memory(session_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL,
        "stream": False,
        "messages": messages,
        "options": {
            "temperature": 0.35,
        },
    }

    body = json.dumps(payload).encode("utf-8")
    ollama_request = Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(ollama_request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    answer = data.get("message", {}).get("content") or "Nao consegui gerar uma resposta agora."
    remember(session_id, "user", user_message)
    remember(session_id, "assistant", answer)
    return answer


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.post("/chat")
def chat():
    body = request.get_json(silent=True) or {}
    user_message = str(body.get("message", "")).strip()
    session_id = normalize_session_id(body.get("sessionId"))

    if not user_message:
        return jsonify({"error": "Escreva uma pergunta sobre React."}), 400

    if len(user_message) > 4000:
        return jsonify({"error": "Mensagem muito grande. Envie uma pergunta menor."}), 413

    try:
        answer = ask_ollama(session_id, user_message)
        return jsonify({"answer": answer, "memorySize": len(get_memory(session_id))})
    except (TimeoutError, URLError, json.JSONDecodeError) as error:
        app.logger.exception("Erro ao falar com o Ollama: %s", error)
        return (
            jsonify(
                {
                    "error": "Nao consegui falar com o Ollama. Confira se o Ollama esta aberto e se o modelo minimax-m2.5:cloud esta disponivel."
                }
            ),
            500,
        )


@app.post("/memory/clear")
def clear_memory():
    body = request.get_json(silent=True) or {}
    session_id = normalize_session_id(body.get("sessionId"))
    CONVERSATION_MEMORY.pop(session_id, None)
    return jsonify({"ok": True})


@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.get("/roadmap")
def roadmap():
    return send_from_directory(ROOT, "roadmap.html")


@app.get("/<path:file_path>")
def static_files(file_path):
    requested = (ROOT / file_path).resolve()

    if ROOT not in requested.parents and requested != ROOT:
        return "Forbidden", 403

    if not requested.is_file():
        return "Arquivo nao encontrado.", 404

    return send_from_directory(ROOT, file_path)


if __name__ == "__main__":
    print(f"ReactIA rodando em http://localhost:{PORT}")
    print(f"Modelo Ollama: {MODEL}")
    app.run(host="127.0.0.1", port=PORT, debug=os.getenv("FLASK_DEBUG") == "1")
