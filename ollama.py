import json
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MODEL = os.getenv("OLLAMA_MODEL", "minimax-m2.5:cloud")
LOCAL_OLLAMA_URL = "http://localhost:11434/api/chat"
CLOUD_OLLAMA_URL = "https://ollama.com/api/chat"
OLLAMA_URL = os.getenv("OLLAMA_URL") or (
    CLOUD_OLLAMA_URL if os.getenv("VERCEL") else LOCAL_OLLAMA_URL
)


def _headers_for_url(url):
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OLLAMA_API_KEY")
    parsed = urlparse(url)

    if api_key and parsed.hostname == "ollama.com":
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def ask_ollama(messages, *, temperature=0.35, timeout=60):
    payload = {
        "model": MODEL,
        "stream": False,
        "messages": messages,
        "options": {
            "temperature": temperature,
        },
    }

    ollama_request = Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers_for_url(OLLAMA_URL),
        method="POST",
    )

    with urlopen(ollama_request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("message", {}).get("content") or "Nao consegui gerar uma resposta agora."
