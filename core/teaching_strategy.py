"""AI School OS — Phase 4.3 Teaching Strategy.

Selects a teaching strategy for a lesson based on student state and
difficulty.  Pure logic — no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TeachingStrategy:
    """A selected teaching strategy.

    Attributes
    ----------
    name:
        Strategy identifier (e.g. ``"explain_first"``, ``"socratic"``,
        ``"step_by_step"``, ``"storytelling"``, ``"visual"``,
        ``"practice_first"``, ``"revision"``, ``"mission_mode"``,
        ``"challenge"``).
    description:
        Human-readable description of when to use this strategy.
    steps:
        Ordered list of instructional steps.
    priority:
        Priority score (higher = more preferred).
    """

    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    priority: int = 0


class StrategySelector:
    """Selects the best teaching strategy for a given student state.

    Selection rules are deterministic and based on difficulty level,
    student strengths/weaknesses, and mission progress.
    """

    # ------------------------------------------------------------------
    # Strategy registry
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._strategies: Dict[str, TeachingStrategy] = {
            "explain_first": TeachingStrategy(
                name="explain_first",
                description="Present the concept clearly before asking questions.",
                steps=["Introduce topic", "Explain core concept", "Check understanding"],
                priority=5,
            ),
            "socratic": TeachingStrategy(
                name="socratic",
                description="Guide the student through questions rather than direct answers.",
                steps=["Ask leading question", "Evaluate response", "Refine question", "Reveal concept"],
                priority=6,
            ),
            "step_by_step": TeachingStrategy(
                name="step_by_step",
                description="Break the topic into small, sequential steps.",
                steps=["Step 1: Prerequisite", "Step 2: Core idea", "Step 3: Worked example", "Step 4: Practice"],
                priority=7,
            ),
            "storytelling": TeachingStrategy(
                name="storytelling",
                description="Teach through narrative and real-world analogies.",
                steps=["Set context", "Tell story", "Extract lesson", "Apply to topic"],
                priority=4,
            ),
            "visual": TeachingStrategy(
                name="visual",
                description="Use diagrams, sketches, and visual explanations.",
                steps=["Show visual", "Explain elements", "Connect to concept", "Practice drawing"],
                priority=5,
            ),
            "practice_first": TeachingStrategy(
                name="practice_first",
                description="Let the student try first, then explain mistakes.",
                steps=["Attempt problem", "Review errors", "Explain correction", "Retry"],
                priority=6,
            ),
            "revision": TeachingStrategy(
                name="revision",
                description="Review previously learned material before introducing new content.",
                steps=["Recap previous lesson", "Identify gaps", "Reinforce weak areas", "Introduce new material"],
                priority=4,
            ),
            "mission_mode": TeachingStrategy(
                name="mission_mode",
                description="Focus tightly on completing the current mission objective.",
                steps=["State mission goal", "Cover required topics", "Verify mission criteria", "Celebrate completion"],
                priority=8,
            ),
            "challenge": TeachingStrategy(
                name="challenge",
                description="Push the student with harder problems to stretch ability.",
                steps=["Present challenge", "Allow struggle", "Provide hint", "Reveal solution"],
                priority=7,
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def select(
        self,
        difficulty: str,
        weak_topics: list[str],
        strong_topics: list[str],
        mission_progress: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeachingStrategy:
        """Select the best teaching strategy.

        Parameters
        ----------
        difficulty:
            The assessed difficulty level.
        weak_topics:
            Topics the student struggles with.
        strong_topics:
            Topics the student has mastered.
        mission_progress:
            Progress toward the current mission (0 to 100).
        context:
            Additional routing context (unused here, reserved for
            future extensions).

        Returns
        -------
        TeachingStrategy
            The selected strategy.
        """
        ctx = context or {}

        # Mission mode takes priority when a mission is active and
        # progress is substantial but not complete.
        if 20.0 < mission_progress < 95.0:
            return self._strategies["mission_mode"]

        # High difficulty with many weak topics -> step-by-step.
        if difficulty in ("beginner", "easy") and len(weak_topics) > len(strong_topics):
            return self._strategies["step_by_step"]

        # Advanced/expert with strong foundation -> challenge.
        if difficulty in ("advanced", "expert") and len(strong_topics) > 2:
            return self._strategies["challenge"]

        # Student has many weak topics -> revision first.
        if len(weak_topics) >= 3 and len(strong_topics) < 2:
            return self._strategies["revision"]

        # Default: explain-first for balanced students.
        return self._strategies["explain_first"]

    def list_strategies(self) -> list[str]:
        """Return all available strategy names."""
        return list(self._strategies.keys())

    def get_strategy(self, name: str) -> Optional[TeachingStrategy]:
        """Return a registered strategy by name, or ``None``."""
        return self._strategies.get(name)
