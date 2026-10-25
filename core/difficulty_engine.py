"""AI School OS — Phase 4.3 Difficulty Engine.

Determines the appropriate lesson difficulty for a student and
computes the recommended XP reward.  Pure logic — no AI calls, no
database writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.memory import Memory
from core.student_model import StudentModel


@dataclass
class DifficultyAssessment:
    """Result of a difficulty assessment.

    Attributes
    ----------
    level:
        One of ``"beginner"``, ``"easy"``, ``"medium"``,
        ``"advanced"``, ``"expert"``.
    confidence:
        Confidence score between 0.0 and 1.0.
    weak_count:
        Number of weak topics considered.
    strong_count:
        Number of strong topics considered.
    xp_reward:
        Recommended XP reward for completing a lesson at this level.
    """

    level: str
    confidence: float = 0.5
    weak_count: int = 0
    strong_count: int = 0
    xp_reward: int = 25


class DifficultyEngine:
    """Computes lesson difficulty and XP rewards.

    The engine is intentionally stateless: it reads data through an
    injected :class:`Memory` instance and returns computed values.
    """

    # ------------------------------------------------------------------
    # Difficulty level mapping
    # ------------------------------------------------------------------
    _LEVEL_ORDER = ["beginner", "easy", "medium", "advanced", "expert"]

    _XP_MAP = {
        "beginner": 10,
        "easy": 15,
        "medium": 25,
        "advanced": 40,
        "expert": 60,
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def assess(
        self,
        student_id: int,
        subject_id: str,
        memory: Memory,
    ) -> DifficultyAssessment:
        """Determine the appropriate difficulty for a student in a subject.

        Parameters
        ----------
        student_id:
            The student being assessed.
        subject_id:
            The subject being studied.
        memory:
            Memory instance for reading weak/strong topics.

        Returns
        -------
        DifficultyAssessment
            The computed difficulty level, confidence, and XP reward.
        """
        weak = memory.get_weak_topics(student_id, subject_id)
        strong = memory.get_strong_topics(student_id, subject_id)

        weak_count = len(weak)
        strong_count = len(strong)

        level = self._determine_level(weak_count, strong_count)
        confidence = self._compute_confidence(weak_count, strong_count)
        xp_reward = self._XP_MAP.get(level, 25)

        return DifficultyAssessment(
            level=level,
            confidence=confidence,
            weak_count=weak_count,
            strong_count=strong_count,
            xp_reward=xp_reward,
        )

    def assess_from_model(
        self,
        model: StudentModel,
    ) -> DifficultyAssessment:
        """Assess difficulty from an existing :class:`StudentModel`.

        Parameters
        ----------
        model:
            A pre-built student model.

        Returns
        -------
        DifficultyAssessment
        """
        weak_count = len(model.weak_topics)
        strong_count = len(model.strong_topics)
        level = self._determine_level(weak_count, strong_count)
        confidence = self._compute_confidence(weak_count, strong_count)
        xp_reward = self._XP_MAP.get(level, 25)

        return DifficultyAssessment(
            level=level,
            confidence=confidence,
            weak_count=weak_count,
            strong_count=strong_count,
            xp_reward=xp_reward,
        )

    def compute_xp_reward(
        self,
        lesson_completed: bool,
        difficulty: str,
        streak_bonus: int = 0,
    ) -> int:
        """Compute XP points for completing (or attempting) a lesson.

        Delegates to :class:`core.learning.LearningEngine`-compatible
        logic but is self-contained here so the Teacher Engine does not
        depend on the learning engine for XP.

        Parameters
        ----------
        lesson_completed:
            Whether the lesson was successfully completed.
        difficulty:
            The difficulty level of the lesson.
        streak_bonus:
            Extra XP from the student's streak.

        Returns
        -------
        int
            XP points to award.
        """
        if not lesson_completed:
            return max(0, streak_bonus)
        return self._XP_MAP.get(difficulty, 25) + streak_bonus

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _determine_level(weak_count: int, strong_count: int) -> str:
        """Map weak/strong topic counts to a difficulty level."""
        if weak_count > strong_count and weak_count > 0:
            return "beginner"
        if strong_count > weak_count and strong_count >= 3:
            return "expert"
        if strong_count > weak_count and strong_count > 0:
            return "advanced"
        if weak_count == 0 and strong_count == 0:
            return "easy"
        if weak_count == 0:
            return "medium"
        return "medium"

    @staticmethod
    def _compute_confidence(weak_count: int, strong_count: int) -> float:
        """Compute confidence in the difficulty assessment."""
        total = weak_count + strong_count
        if total == 0:
            return 0.3
        if total >= 5:
            return 0.9
        if total >= 3:
            return 0.7
        return 0.5
