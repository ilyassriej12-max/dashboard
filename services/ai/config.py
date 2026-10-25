"""AI School OS — Phase 4.2 AI configuration.

Loads environment variables for AI provider configuration.
Supports:

* ``GEMINI_API_KEY`` — API key for Google Gemini
* ``OLLAMA_URL`` — Base URL for Ollama (default ``http://localhost:11434``)
* ``DEFAULT_PROVIDER`` — Primary provider id (default ``"ollama"``)
* ``DEFAULT_MODEL`` — Default model identifier
* ``FALLBACK_PROVIDER`` — Fallback provider id when the primary is unavailable

A ``.env`` file in the project root is loaded automatically if
``python-dotenv`` is installed.
"""

from __future__ import annotations

import os

try:  # python-dotenv is optional but recommended
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover — dotenv not installed
    pass


GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
"""API key for Google Gemini. Empty string if not configured."""

OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
"""Base URL for the Ollama server."""

DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "ollama")
"""Primary provider id used when no explicit preference is given."""

DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3.2")
"""Default model identifier."""

FALLBACK_PROVIDER: str = os.getenv("FALLBACK_PROVIDER", "gemini")
"""Fallback provider id used when the default provider is unavailable."""

PROVIDER_PRIORITIES: dict[str, int] = {
    "ollama": 10,
    "gemini": 5,
}
"""Provider priority scores (higher = preferred)."""
