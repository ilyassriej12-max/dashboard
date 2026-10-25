"""AI School OS — Phase 4.2 AI provider router.

Complete implementation of provider selection with:

* Provider registration with priorities
* Health-aware selection (healthy providers preferred)
* Automatic fallback when the primary provider fails
* Health checking of all registered providers
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.ai.base import AIProvider
from services.ai.config import PROVIDER_PRIORITIES


class ProviderSelection:
    """Result of a provider selection decision."""

    def __init__(
        self,
        provider_id: str,
        fallback_provider_id: Optional[str] = None,
        reasoning: str = "",
    ) -> None:
        self.provider_id = provider_id
        """ID of the selected primary provider."""
        self.fallback_provider_id = fallback_provider_id
        """ID of the fallback provider, if any."""
        self.reasoning = reasoning
        """Human-readable explanation of the selection."""


class AIRouter:
    """Provider-selection engine with health detection and automatic fallback.

    Responsibilities:

    * Register providers with priority scores
    * Select the best healthy provider for a request
    * Select a fallback when the primary provider fails
    * Health-check all providers
    """

    def __init__(self) -> None:
        self._providers: Dict[str, AIProvider] = {}
        """Registry of provider_id -> provider instance."""
        self._provider_priorities: Dict[str, int] = dict(
            PROVIDER_PRIORITIES
        )
        """Provider_id -> priority (higher = preferred)."""
        self._health_cache: Dict[str, bool] = {}
        """Last known health status per provider_id."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, provider: AIProvider, priority: int | None = None) -> None:
        """Register a provider instance under its ``provider_id``.

        Parameters
        ----------
        provider:
            The :class:`AIProvider` instance to register.
        priority:
            Optional priority override.  If omitted, the default from
            :data:`services.ai.config.PROVIDER_PRIORITIES` is used
            (default 0).
        """
        self._providers[provider.provider_id] = provider
        if priority is not None:
            self._provider_priorities[provider.provider_id] = priority
        elif provider.provider_id not in self._provider_priorities:
            self._provider_priorities[provider.provider_id] = 0

    def get_provider(self, provider_id: str) -> AIProvider | None:
        """Return the registered provider for *provider_id*, or ``None``."""
        return self._providers.get(provider_id)

    def list_providers(self) -> List[str]:
        """Return the IDs of all registered providers."""
        return list(self._providers.keys())

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------
    def _healthy_provider_ids(self) -> list[str]:
        """Return provider IDs sorted by priority (healthy first)."""
        healthy = [
            pid
            for pid in self._providers
            if self._health_cache.get(pid, False)
        ]
        if not healthy:
            # Nothing is healthy — fall back to all providers
            healthy = list(self._providers.keys())
        return sorted(
            healthy,
            key=lambda p: self._provider_priorities.get(p, 0),
            reverse=True,
        )

    def select_provider(
        self,
        request_type: str = "general",
        preferred_model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ProviderSelection:
        """Select the best provider for *request_type*.

        Selection logic:

        1. Consider only healthy providers (or all if none are healthy).
        2. If *preferred_model* is given, prefer a provider using that model.
        3. Otherwise pick the highest-priority provider.
        4. Choose a fallback from the remaining healthy providers.

        Returns
        -------
        ProviderSelection
            Routing information — no provider is invoked here.
        """
        sorted_ids = self._healthy_provider_ids()
        if not sorted_ids:
            return ProviderSelection(
                provider_id="",
                fallback_provider_id=None,
                reasoning="No providers registered",
            )

        # If a preferred model is requested, try to match it first.
        primary_id: str | None = None
        if preferred_model:
            for pid in sorted_ids:
                if self._providers[pid].model == preferred_model:
                    primary_id = pid
                    break

        if primary_id is None:
            primary_id = sorted_ids[0]

        remaining = [pid for pid in sorted_ids if pid != primary_id]
        fallback_id = remaining[0] if remaining else None

        reasoning = (
            f"Selected {primary_id} (priority="
            f"{self._provider_priorities.get(primary_id, 0)})"
        )
        if preferred_model:
            reasoning += f", model match={preferred_model}"
        if fallback_id:
            reasoning += f", fallback={fallback_id}"

        return ProviderSelection(
            provider_id=primary_id,
            fallback_provider_id=fallback_id,
            reasoning=reasoning,
        )

    def fallback(
        self,
        failed_provider_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ProviderSelection:
        """Select a fallback provider after *failed_provider_id* errors.

        Returns the next healthy provider by priority, excluding the
        failed one.  Returns an empty ``provider_id`` if none are
        available.
        """
        sorted_ids = self._healthy_provider_ids()
        candidates = [pid for pid in sorted_ids if pid != failed_provider_id]

        if not candidates:
            return ProviderSelection(
                provider_id="",
                fallback_provider_id=None,
                reasoning="No fallback providers available",
            )

        fallback_id = candidates[0]
        return ProviderSelection(
            provider_id=fallback_id,
            fallback_provider_id=candidates[1] if len(candidates) > 1 else None,
            reasoning=f"Fallback after {failed_provider_id} failure",
        )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    async def health_check(self) -> Dict[str, bool]:
        """Return a mapping of provider_id -> health status.

        Caches results in :attr:`_health_cache` for use by
        :meth:`select_provider`.
        """
        results: Dict[str, bool] = {}
        for pid, provider in self._providers.items():
            try:
                results[pid] = await provider.health()
            except Exception:
                results[pid] = False
        self._health_cache = results
        return results
