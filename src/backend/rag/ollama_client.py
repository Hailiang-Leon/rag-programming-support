from __future__ import annotations

import httpx

from src.backend.config import settings


class OllamaGenerationError(RuntimeError):
    """Raised when the local Ollama model cannot generate a response."""


def generate_with_ollama(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    timeout_seconds: float = 120.0,
) -> str:
    """
    Send a prompt to the local Ollama generation API and return the generated text.
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty.")

    selected_model = model or settings.ollama_model
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    try:
        response = httpx.post(url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise OllamaGenerationError(
            f"Failed to call Ollama at {url}. Check that Ollama is running and the model exists."
        ) from error

    data = response.json()
    generated_text = data.get("response", "").strip()

    if not generated_text:
        raise OllamaGenerationError("Ollama returned an empty response.")

    return generated_text
