import json
import os
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


MODEL = os.getenv("OLLAMA_MODEL", "minimax-m2.5:cloud")
LOCAL_OLLAMA_URL = "http://localhost:11434/api/chat"
CLOUD_OLLAMA_URL = "https://ollama.com/api/chat"
OLLAMA_URL = os.getenv("OLLAMA_URL") or (
    CLOUD_OLLAMA_URL if os.getenv("VERCEL") or os.getenv("OLLAMA_API_KEY") else LOCAL_OLLAMA_URL
)


class OllamaConfigError(RuntimeError):
    pass


class OllamaAPIError(RuntimeError):
    pass


def is_cloud_url(url):
    return urlparse(url).hostname == "ollama.com"


def _headers_for_url(url):
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OLLAMA_API_KEY")

    if api_key and is_cloud_url(url):
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def validate_ollama_config():
    if os.getenv("VERCEL") and not is_cloud_url(OLLAMA_URL):
        raise OllamaConfigError(
            "No Vercel, OLLAMA_URL precisa apontar para um endpoint publico. "
            "Nao use localhost:11434 em producao."
        )

    if is_cloud_url(OLLAMA_URL) and not os.getenv("OLLAMA_API_KEY"):
        raise OllamaConfigError(
            "Configure OLLAMA_API_KEY nas variaveis de ambiente da Vercel."
        )


def ask_ollama(messages, *, temperature=0.35, timeout=60):
    validate_ollama_config()

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

    try:
        with urlopen(ollama_request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise OllamaAPIError(
            f"Ollama respondeu com HTTP {error.code}: {details[:500]}"
        ) from error

    return data.get("message", {}).get("content") or "Nao consegui gerar uma resposta agora."
