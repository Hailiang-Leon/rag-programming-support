from __future__ import annotations

import httpx

from src.backend.config import settings


class OllamaGenerationError(RuntimeError):
    """Raised when the local Ollama model cannot generate a response."""


def generate_with_ollama(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    timeout_seconds: float | None = None,
) -> str:
    """
    Send a prompt to the local Ollama generation API and return
    the generated response text.
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty.")

    selected_model = model or settings.ollama_model

    selected_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else settings.ollama_timeout_seconds
    )

    url = (
        f"{settings.ollama_base_url.rstrip('/')}"
        "/api/generate"
    )

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "think": settings.ollama_think,
        "keep_alive": settings.ollama_keep_alive,
        "options": {
            "temperature": temperature,
            "num_predict": settings.ollama_num_predict,
        },
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            timeout=selected_timeout,
        )
        response.raise_for_status()

    except httpx.TimeoutException as error:
        raise OllamaGenerationError(
            "Ollama generation exceeded "
            f"{selected_timeout:.0f} seconds for model "
            f"'{selected_model}'."
        ) from error

    except httpx.HTTPError as error:
        raise OllamaGenerationError(
            f"Failed to call Ollama at {url}. "
            "Check that Ollama is running and that "
            f"model '{selected_model}' is installed."
        ) from error

    data = response.json()
    generated_text = data.get("response", "").strip()

    if not generated_text:
        raise OllamaGenerationError(
            "Ollama returned an empty response."
        )

    return generated_text
