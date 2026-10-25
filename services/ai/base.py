"""AI School OS — Phase 4.1 AI provider interface.

Defines the abstract contract that every AI provider (Gemini, Ollama,
OpenAI, …) must implement.  This module contains *only* method
signatures — no provider implementation, no network calls, no API keys.

Future phases will create concrete subclasses of :class:`AIProvider`
and register them via :mod:`services.ai.router`.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Optional


class AIProvider:
    """Abstract base class for AI providers.

    Concrete providers implement :meth:`generate`, :meth:`stream`, and
    :meth:`health`.  No LLM call happens here — this is purely a
    type-safe interface for Phase 4.2+.
    """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    provider_id: str
    """Unique identifier for this provider (e.g. ``"gemini"``)."""

    model: str
    """Model identifier used by this provider."""

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a completion for *prompt*.

        Parameters
        ----------
        prompt:
            The user-facing prompt text.
        system_instruction:
            Optional system-level instruction to prepend.
        temperature:
            Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_tokens:
            Maximum number of tokens to generate.
        kwargs:
            Provider-specific extra parameters.

        Returns
        -------
        dict
            A provider-normalised response dict with at least a
            ``"text"`` key containing the generated text.
        """
        raise NotImplementedError

    async def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream a completion for *prompt*.

        Yields partial result dicts as tokens arrive.  Each yielded
        dict contains at least a ``"delta"`` key with the new text
        fragment and an optional ``"done"`` flag.
        """
        raise NotImplementedError

    async def health(self) -> bool:
        """Return ``True`` if the provider is reachable and healthy.

        Used by :mod:`services.ai.router` for fallback decisions.
        """
        raise NotImplementedError
