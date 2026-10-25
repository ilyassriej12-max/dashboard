"""AI School OS — Phase 4.2 Gemini AI provider.

Implements :class:`services.ai.base.AIProvider` for Google Gemini using
the REST API (no Python SDK required — uses :mod:`httpx` which is already
a FastAPI dependency).
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from services.ai.base import AIProvider
from services.ai.config import DEFAULT_MODEL, GEMINI_API_KEY


class GeminiProvider(AIProvider):
    """Gemini provider via the Generative Language REST API.

    Endpoint:
        POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    """

    provider_id: str = "gemini"
    model: str = DEFAULT_MODEL

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ) -> None:
        self.model = model or DEFAULT_MODEL
        self.api_key = api_key or GEMINI_API_KEY
        self.base_url = base_url.rstrip("/")

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
        """Generate a completion via Gemini's ``generateContent`` REST API."""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        parts: list[dict[str, Any]] = []
        if system_instruction:
            parts.append({"text": system_instruction})
        parts.append({"text": prompt})

        body: dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": temperature},
        }
        if max_tokens:
            body["generationConfig"]["maxOutputTokens"] = max_tokens

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, headers=headers, params=params, json=body, timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()

        text = ""
        if data.get("candidates"):
            text = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get(
                "text", ""
            )

        usage = data.get("usageMetadata", {})
        return {
            "text": text,
            "provider": self.provider_id,
            "model": self.model,
            "tokens": usage.get("totalTokenCount"),
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
        """Stream completion tokens via Gemini's ``streamGenerateContent`` SSE endpoint."""
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        parts: list[dict[str, Any]] = []
        if system_instruction:
            parts.append({"text": system_instruction})
        parts.append({"text": prompt})

        body: dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": temperature},
        }
        if max_tokens:
            body["generationConfig"]["maxOutputTokens"] = max_tokens

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", url, headers=headers, params=params, json=body, timeout=60.0
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[len("data:") :].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    candidates = chunk.get("candidates", [])
                    if candidates:
                        delta = (
                            candidates[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        if delta:
                            yield {"delta": delta, "done": False}
        yield {"delta": "", "done": True}

    # ------------------------------------------------------------------
    # health
    # ------------------------------------------------------------------
    async def health(self) -> bool:
        """Return ``True`` if the Gemini model endpoint is reachable."""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/models/{self.model}",
                    params={"key": self.api_key},
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False
