import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, send_from_directory

from ollama import MODEL, OLLAMA_URL, OllamaAPIError, OllamaConfigError, ask_ollama


ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "3001"))
MAX_MEMORY_MESSAGES = 24
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ENABLED = all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY])

DEFAULT_NOTES = [
    "O aluno esta usando a Tunix IA como mentora de Linux em pt-BR.",
    "Prefere explicacoes praticas, diretas e com exemplos curtos.",
]

SYSTEM_PROMPT = f"""
Voce e a Tunix IA, uma IA especialista em Linux, terminal, servidores e distros.
Ajude somente com Linux e seu ecossistema: terminal, comandos, shell script,
permissoes, usuarios, pacotes, systemd, redes, servidores, seguranca basica,
virtualizacao, WSL e comparacao entre distros.

Regras:
- Use sempre fontes validas para estudo como documentacoes oficiais e explicacoes atuais.
- Responda em pt-BR.
- Use exemplos praticos e curtos quando ajudar.
- Quando o usuario pedir orientacao de estudo, siga este roadmap:
  1. Base do Linux: terminal, arquivos, diretorios e comandos essenciais.
  2. Distros e ambiente: Ubuntu, Debian, Fedora, Arch, Mint, servidores, WSL e VMs.
  3. Pacotes e sistema: apt, dnf, pacman, atualizacoes, systemctl e journalctl.
  4. Permissoes e usuarios: sudo, grupos, chmod, chown e seguranca basica.
  5. Shell e automacao: Bash, pipes, redirecionamento, scripts e cron.
  6. Servidor final: SSH, firewall, servicos web, logs, backups e monitoramento.
- Sugira o proximo passo do roadmap quando isso for util para o aluno.
- Se o usuario pedir algo fora de Linux, distros, terminal, servidores ou administracao Linux,
  explique com gentileza que voce so pode ajudar nesse tema.
- Nao mencione nem use outro provedor/modelo de IA. O modelo permitido e {MODEL}.
- Use a memoria persistente recebida no contexto para manter continuidade entre
  mensagens e reinicios. Se houver conflito, priorize a mensagem mais recente.
""".strip()

app = Flask(__name__, static_folder=None)


class SupabaseConfigError(RuntimeError):
    pass


class SupabaseAPIError(RuntimeError):
    pass


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_session_id(value):
    session_id = str(value or "default").strip()
    safe = "".join(char for char in session_id if char.isalnum() or char in "-_")
    return safe[:80] or "default"


def require_supabase_config():
    if SUPABASE_ENABLED:
        return

    raise SupabaseConfigError(
        "Configure SUPABASE_URL, SUPABASE_ANON_KEY e SUPABASE_SERVICE_ROLE_KEY."
    )


def read_json_response(response):
    text = response.read().decode("utf-8")
    return json.loads(text) if text else None


def supabase_rest(path, *, method="GET", payload=None, prefer=None):
    require_supabase_config()

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Accept": "application/json",
    }

    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    if prefer:
        headers["Prefer"] = prefer

    supabase_request = Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(supabase_request, timeout=30) as response:
            return read_json_response(response)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise SupabaseAPIError(
            f"Supabase REST respondeu HTTP {error.code}: {details[:500]}"
        ) from error


def get_current_user():
    require_supabase_config()

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()

    if not token or token == auth_header:
        return None

    user_request = Request(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(user_request, timeout=20) as response:
            user = read_json_response(response)
    except HTTPError:
        return None

    if not isinstance(user, dict) or not user.get("id"):
        return None

    return {
        "id": user["id"],
        "email": user.get("email") or "",
    }


def auth_error_response():
    return jsonify({"error": "Entre na sua conta para continuar."}), 401


def eq(value):
    return quote(str(value), safe="")


def session_title(session_id, messages):
    for message in messages:
        if message.get("role") == "user" and str(message.get("content", "")).strip():
            title = " ".join(str(message["content"]).split())
            return title[:54] + ("..." if len(title) > 54 else "")

    return "Nova conversa" if session_id != "default" else "Conversa principal"


def get_conversation_record(user_id, session_id):
    rows = supabase_rest(
        "tunix_conversations"
        f"?select=id,title,message_count,created_at,updated_at"
        f"&user_id=eq.{eq(user_id)}&id=eq.{eq(session_id)}&limit=1"
    )
    return rows[0] if rows else None


def get_recent_messages(user_id, session_id, limit=MAX_MEMORY_MESSAGES):
    rows = supabase_rest(
        "tunix_messages"
        f"?select=role,content,created_at"
        f"&user_id=eq.{eq(user_id)}&conversation_id=eq.{eq(session_id)}"
        f"&order=created_at.asc&limit={int(limit)}"
    )
    return rows or []


def ensure_conversation(user_id, session_id):
    existing = get_conversation_record(user_id, session_id)

    if existing:
        return existing

    created = supabase_rest(
        "tunix_conversations",
        method="POST",
        payload={
            "id": session_id,
            "user_id": user_id,
            "title": "Nova conversa",
            "message_count": 0,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        },
        prefer="return=representation",
    )
    return created[0] if created else get_conversation_record(user_id, session_id)


def update_conversation(user_id, session_id, *, title, message_count):
    supabase_rest(
        "tunix_conversations"
        f"?user_id=eq.{eq(user_id)}&id=eq.{eq(session_id)}",
        method="PATCH",
        payload={
            "title": title,
            "message_count": message_count,
            "updated_at": utc_now(),
        },
        prefer="return=minimal",
    )


def remember_pair(user_id, session_id, user_message, assistant_answer):
    conversation = ensure_conversation(user_id, session_id)
    current_count = int(conversation.get("message_count") or 0)

    supabase_rest(
        "tunix_messages",
        method="POST",
        payload=[
            {
                "conversation_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": user_message,
                "created_at": utc_now(),
            },
            {
                "conversation_id": session_id,
                "user_id": user_id,
                "role": "assistant",
                "content": assistant_answer,
                "created_at": utc_now(),
            },
        ],
        prefer="return=minimal",
    )

    if current_count:
        title = conversation.get("title") or "Conversa Linux"
    else:
        title = session_title(session_id, [{"role": "user", "content": user_message}])

    update_conversation(
        user_id,
        session_id,
        title=title,
        message_count=current_count + 2,
    )


def serialize_conversation(record, include_messages=False, messages=None):
    data = {
        "id": record.get("id"),
        "title": record.get("title") or "Nova conversa",
        "messages": record.get("message_count") or 0,
        "updatedAt": record.get("updated_at"),
        "createdAt": record.get("created_at"),
    }

    if include_messages:
        data["items"] = messages or []

    return data


def build_memory_context(user_id, session_id, recent_messages):
    lines = ["Memoria persistente da Tunix IA:"]
    lines.append("Notas fixas:")
    lines.extend(f"- {note}" for note in DEFAULT_NOTES)

    if recent_messages:
        lines.append(
            f"Historico recente salvo: {len(recent_messages)} mensagens anteriores nesta sessao."
        )

    return "\n".join(lines)


def ask_tunix(user_id, session_id, user_message):
    recent_messages = get_recent_messages(user_id, session_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": build_memory_context(user_id, session_id, recent_messages),
        },
    ]
    messages.extend(
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in recent_messages
    )
    messages.append({"role": "user", "content": user_message})

    answer = ask_ollama(messages)
    remember_pair(user_id, session_id, user_message, answer)
    return answer


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.errorhandler(SupabaseConfigError)
def handle_supabase_config_error(error):
    app.logger.warning("Configuracao invalida do Supabase: %s", error)
    return jsonify({"error": str(error)}), 500


@app.errorhandler(SupabaseAPIError)
def handle_supabase_api_error(error):
    app.logger.exception("Erro ao falar com o Supabase: %s", error)
    return jsonify({"error": "Nao consegui acessar suas conversas agora."}), 500


@app.get("/auth/config")
def auth_config():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return jsonify(
            {
                "enabled": False,
                "error": "Configure SUPABASE_URL e SUPABASE_ANON_KEY.",
            }
        )

    return jsonify(
        {
            "enabled": True,
            "supabaseUrl": SUPABASE_URL,
            "supabaseAnonKey": SUPABASE_ANON_KEY,
        }
    )


@app.post("/chat")
def chat():
    user = get_current_user()

    if not user:
        return auth_error_response()

    body = request.get_json(silent=True) or {}
    user_message = str(body.get("message", "")).strip()
    session_id = normalize_session_id(body.get("sessionId"))

    if not user_message:
        return jsonify({"error": "Escreva uma pergunta sobre Linux."}), 400

    if len(user_message) > 4000:
        return jsonify({"error": "Mensagem muito grande. Envie uma pergunta menor."}), 413

    try:
        answer = ask_tunix(user["id"], session_id, user_message)
        conversation = get_conversation_record(user["id"], session_id) or {}
        return jsonify(
            {
                "answer": answer,
                "memorySize": conversation.get("message_count") or 0,
            }
        )
    except SupabaseConfigError as error:
        app.logger.exception("Configuracao invalida do Supabase: %s", error)
        return jsonify({"error": str(error)}), 500
    except SupabaseAPIError as error:
        app.logger.exception("Erro ao falar com o Supabase: %s", error)
        return jsonify({"error": "Nao consegui salvar sua conversa agora."}), 500
    except OllamaConfigError as error:
        app.logger.exception("Configuracao invalida do Ollama: %s", error)
        return jsonify({"error": str(error)}), 500
    except (TimeoutError, URLError, json.JSONDecodeError, OllamaAPIError) as error:
        app.logger.exception("Erro ao falar com o Ollama: %s", error)
        return (
            jsonify(
                {
                    "error": "Nao consegui falar com o Ollama. No Vercel, configure OLLAMA_API_KEY e use um modelo cloud disponivel."
                }
            ),
            500,
        )


@app.post("/memory/clear")
def clear_memory():
    user = get_current_user()

    if not user:
        return auth_error_response()

    body = request.get_json(silent=True) or {}
    session_id = normalize_session_id(body.get("sessionId"))

    supabase_rest(
        "tunix_conversations"
        f"?user_id=eq.{eq(user['id'])}&id=eq.{eq(session_id)}",
        method="DELETE",
        prefer="return=minimal",
    )
    return jsonify({"ok": True})


@app.post("/conversation/delete")
def delete_conversation():
    user = get_current_user()

    if not user:
        return auth_error_response()

    body = request.get_json(silent=True) or {}
    session_id = normalize_session_id(body.get("sessionId"))

    supabase_rest(
        "tunix_conversations"
        f"?user_id=eq.{eq(user['id'])}&id=eq.{eq(session_id)}",
        method="DELETE",
        prefer="return=minimal",
    )
    return jsonify({"ok": True})


@app.get("/conversations")
def conversations():
    user = get_current_user()

    if not user:
        return auth_error_response()

    rows = supabase_rest(
        "tunix_conversations"
        f"?select=id,title,message_count,created_at,updated_at"
        f"&user_id=eq.{eq(user['id'])}&order=updated_at.desc"
    )
    return jsonify(
        {"conversations": [serialize_conversation(row) for row in rows or []]}
    )


@app.get("/conversation")
def conversation():
    user = get_current_user()

    if not user:
        return auth_error_response()

    session_id = normalize_session_id(request.args.get("sessionId"))
    record = get_conversation_record(user["id"], session_id)

    if not record:
        record = {
            "id": session_id,
            "title": "Nova conversa",
            "message_count": 0,
            "created_at": None,
            "updated_at": None,
        }
        return jsonify(serialize_conversation(record, include_messages=True, messages=[]))

    messages = get_recent_messages(user["id"], session_id)
    return jsonify(serialize_conversation(record, include_messages=True, messages=messages))


@app.get("/memory")
def memory_status():
    user = get_current_user()

    if not user:
        return auth_error_response()

    session_id = normalize_session_id(request.args.get("sessionId"))
    record = get_conversation_record(user["id"], session_id)
    return jsonify(
        {
            "messages": (record or {}).get("message_count") or 0,
            "notes": DEFAULT_NOTES,
            "updatedAt": (record or {}).get("updated_at"),
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
    print(f"Tunix IA rodando em http://localhost:{PORT}")
    print(f"Modelo Ollama: {MODEL}")
    print(f"Endpoint Ollama: {OLLAMA_URL}")
    print(f"Supabase configurado: {'sim' if SUPABASE_ENABLED else 'nao'}")
    app.run(host="127.0.0.1", port=PORT, debug=os.getenv("FLASK_DEBUG") == "1")
