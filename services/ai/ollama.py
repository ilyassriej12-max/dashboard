"""AI School OS — Phase 4.2 Ollama AI provider.

Implements :class:`services.ai.base.AIProvider` for Ollama using its
REST API (no Python SDK required — uses :mod:`httpx`).
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from services.ai.base import AIProvider
from services.ai.config import DEFAULT_MODEL, OLLAMA_URL


class OllamaProvider(AIProvider):
    """Ollama provider via the Ollama REST API.

    Endpoints:
        POST {OLLAMA_URL}/api/generate   (non-streaming)
        POST {OLLAMA_URL}/api/generate   (streaming, NDJSON)
        GET  {OLLAMA_URL}/api/tags       (health check)
    """

    provider_id: str = "ollama"
    model: str = DEFAULT_MODEL

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model or DEFAULT_MODEL
        self.base_url = (base_url or OLLAMA_URL).rstrip("/")

    # ------------------------------------------------------------------
    # generate
    # ------------------------------------------------------------------
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a completion via Ollama's ``/api/generate`` (non-streaming)."""
        url = f"{self.base_url}/api/generate"
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
        }
        if system_instruction:
            body["system"] = system_instruction
        if max_tokens is not None:
            body["num_predict"] = max_tokens

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=body, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()

        return {
            "text": data.get("response", ""),
            "provider": self.provider_id,
            "model": self.model,
            "tokens": data.get("eval_count"),
            "raw": data,
        }

    # ------------------------------------------------------------------
    # stream
    # ------------------------------------------------------------------
    async def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream completion tokens via Ollama's ``/api/generate`` with ``stream: true``."""
        url = f"{self.base_url}/api/generate"
        body: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "temperature": temperature,
        }
        if system_instruction:
            body["system"] = system_instruction
        if max_tokens is not None:
            body["num_predict"] = max_tokens

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", url, json=body, timeout=60.0
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("done"):
                        yield {"delta": "", "done": True}
                        return
                    delta = chunk.get("response", "")
                    if delta:
                        yield {"delta": delta, "done": False}

    # ------------------------------------------------------------------
    # health
    # ------------------------------------------------------------------
    async def health(self) -> bool:
        """Return ``True`` if the Ollama server is reachable."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/api/tags", timeout=10.0
                )
                return resp.status_code == 200
        except Exception:
            return False
