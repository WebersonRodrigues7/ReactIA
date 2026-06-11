import os
from pathlib import Path
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen
import json

from flask import Flask, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "3001"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = "minimax-m2.5:cloud"
MAX_MEMORY_MESSAGES = 24
MEMORY_FILE = ROOT / "memory_base.json"
MEMORY_STATE = {"sessions": {}}

SYSTEM_PROMPT = f"""
Voce e a ReactIA, uma IA especialista em desenvolvimento React.
Ajude somente com React e seu ecossistema: componentes, hooks, estado,
props, roteamento, formularios, bibliotecas React, Vite, Next.js, testes,
estilizacao e boas praticas de frontend React.

Regras: a
- Use sempre fontes válidas para estudo como documentações e explicações de 2025 para frente
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
- Use a memoria persistente recebida no contexto para manter continuidade entre
  mensagens e reinicios. Se houver conflito, priorize a mensagem mais recente.
""".strip()

app = Flask(__name__, static_folder=None)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_memory_state():
    global MEMORY_STATE

    if not MEMORY_FILE.exists():
        return

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        app.logger.warning("Nao foi possivel carregar a base de memoria.")
        return

    if isinstance(data, dict) and isinstance(data.get("sessions"), dict):
        MEMORY_STATE = data


def save_memory_state():
    try:
        MEMORY_FILE.write_text(
            json.dumps(MEMORY_STATE, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as error:
        app.logger.warning("Nao foi possivel salvar a base de memoria: %s", error)


def normalize_session_id(value):
    session_id = str(value or "default").strip()
    safe = "".join(char for char in session_id if char.isalnum() or char in "-_")
    return safe[:80] or "default"


def get_memory(session_id):
    session = MEMORY_STATE["sessions"].setdefault(
        session_id,
        {
            "createdAt": utc_now(),
            "updatedAt": utc_now(),
            "messages": [],
            "notes": [
                "O aluno esta usando a ReactIA como mentora de React em pt-BR.",
                "Prefere explicacoes praticas, diretas e com exemplos curtos.",
            ],
        },
    )
    return session


def remember(session_id, role, content):
    session = get_memory(session_id)
    session["messages"].append(
        {
            "role": role,
            "content": content,
            "createdAt": utc_now(),
        }
    )
    del session["messages"][:-MAX_MEMORY_MESSAGES]
    session["updatedAt"] = utc_now()
    save_memory_state()


def session_title(session_id, session):
    for message in session.get("messages", []):
        if message.get("role") == "user" and str(message.get("content", "")).strip():
            title = " ".join(str(message["content"]).split())
            return title[:54] + ("..." if len(title) > 54 else "")

    return "Nova conversa" if session_id != "default" else "Conversa principal"


def serialize_session(session_id, session, include_messages=False):
    data = {
        "id": session_id,
        "title": session_title(session_id, session),
        "messages": len(session.get("messages", [])),
        "updatedAt": session.get("updatedAt"),
        "createdAt": session.get("createdAt"),
    }

    if include_messages:
        data["items"] = session.get("messages", [])

    return data


def build_memory_context(session_id):
    session = get_memory(session_id)
    notes = session.get("notes", [])

    if not notes and not session.get("messages"):
        return ""

    lines = ["Memoria persistente da ReactIA:"]

    if notes:
        lines.append("Notas fixas:")
        lines.extend(f"- {note}" for note in notes[:8])

    if session.get("messages"):
        lines.append(
            f"Historico recente salvo: {len(session['messages'])} mensagens anteriores nesta sessao."
        )

    return "\n".join(lines)


load_memory_state()


def ask_ollama(session_id, user_message):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    memory_context = build_memory_context(session_id)
    if memory_context:
        messages.append({"role": "system", "content": memory_context})
    messages.extend(
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in get_memory(session_id).get("messages", [])
    )
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
        return jsonify(
            {
                "answer": answer,
                "memorySize": len(get_memory(session_id).get("messages", [])),
            }
        )
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
    MEMORY_STATE["sessions"].pop(session_id, None)
    save_memory_state()
    return jsonify({"ok": True})


@app.post("/conversation/delete")
def delete_conversation():
    body = request.get_json(silent=True) or {}
    session_id = normalize_session_id(body.get("sessionId"))
    MEMORY_STATE["sessions"].pop(session_id, None)
    save_memory_state()
    return jsonify({"ok": True})


@app.get("/conversations")
def conversations():
    sessions = [
        serialize_session(session_id, session)
        for session_id, session in MEMORY_STATE.get("sessions", {}).items()
    ]
    sessions.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    return jsonify({"conversations": sessions})


@app.get("/conversation")
def conversation():
    session_id = normalize_session_id(request.args.get("sessionId"))
    session = get_memory(session_id)
    return jsonify(serialize_session(session_id, session, include_messages=True))


@app.get("/memory")
def memory_status():
    session_id = normalize_session_id(request.args.get("sessionId"))
    session = get_memory(session_id)
    return jsonify(
        {
            "messages": len(session.get("messages", [])),
            "notes": session.get("notes", []),
            "updatedAt": session.get("updatedAt"),
        }
    )


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
