"""AI School OS — Phase 4.1 adaptive learning engine.

Pure logic layer that computes difficulty, XP rewards, lesson
completion state, weakness/strength detection, and mission progress.

No UI, no database writes (memory layer handles persistence), no AI
calls — only deterministic learning logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.memory import Memory


class LearningEngine:
    """Computes adaptive learning parameters for a student.

    The engine is intentionally stateless with respect to persistence:
    it reads data through an injected :class:`Memory` instance and
    returns computed values.  The caller decides what to persist.
    """

    # ------------------------------------------------------------------
    # Difficulty
    # ------------------------------------------------------------------
    def compute_difficulty(
        self,
        student_id: int,
        subject_id: str,
        memory: Memory,
    ) -> str:
        """Determine the appropriate difficulty level for a subject.

        Parameters
        ----------
        student_id:
            The student.
        subject_id:
            The subject being studied.
        memory:
            Memory instance for reading weak/strong topics.

        Returns
        -------
        str
            One of ``"beginner"``, ``"intermediate"``, ``"advanced"``.
        """
        weak = memory.get_weak_topics(student_id, subject_id)
        strong = memory.get_strong_topics(student_id, subject_id)

        weak_count = len(weak)
        strong_count = len(strong)

        if weak_count > strong_count and weak_count > 0:
            return "beginner"
        if strong_count > weak_count and strong_count > 0:
            return "advanced"
        return "intermediate"

    # ------------------------------------------------------------------
    # XP rewards
    # ------------------------------------------------------------------
    def compute_xp_reward(
        self,
        lesson_completed: bool,
        difficulty: str,
        streak_bonus: int = 0,
    ) -> int:
        """Compute XP points for completing (or attempting) a lesson.

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
        base = 0
        if not lesson_completed:
            return max(0, streak_bonus)

        difficulty_map = {
            "beginner": 10,
            "intermediate": 25,
            "advanced": 50,
        }
        base = difficulty_map.get(difficulty, 25)
        return base + streak_bonus

    # ------------------------------------------------------------------
    # Lesson completion
    # ------------------------------------------------------------------
    def evaluate_lesson_completion(
        self,
        score: Optional[float],
        passing_threshold: float = 70.0,
    ) -> Dict[str, Any]:
        """Evaluate whether a lesson attempt counts as completed.

        Parameters
        ----------
        score:
            The student's score (0-100), or ``None`` if not attempted.
        passing_threshold:
            Minimum score to pass (default 70).

        Returns
        -------
        dict
            Keys: ``completed`` (bool), ``passed`` (bool), ``score``.
        """
        if score is None:
            return {"completed": False, "passed": False, "score": None}
        passed = score >= passing_threshold
        return {
            "completed": True,
            "passed": passed,
            "score": score,
        }

    # ------------------------------------------------------------------
    # Weakness detection
    # ------------------------------------------------------------------
    def detect_weaknesses(
        self,
        student_id: int,
        subject_id: Optional[str] = None,
        memory: Optional[Memory] = None,
    ) -> List[Dict[str, Any]]:
        """Return detected weak topics for a student.

        If *memory* is supplied, reads from SQLite.  Otherwise returns
        an empty list (no data source configured).
        """
        if memory is None:
            return []
        topics = memory.get_weak_topics(student_id, subject_id)
        return [
            {
                "topic": t["topic"],
                "subject_id": t.get("subject_id"),
                "score": t.get("weakness_score", 0.0),
            }
            for t in topics
        ]

    # ------------------------------------------------------------------
    # Strength detection
    # ------------------------------------------------------------------
    def detect_strengths(
        self,
        student_id: int,
        subject_id: Optional[str] = None,
        memory: Optional[Memory] = None,
    ) -> List[Dict[str, Any]]:
        """Return detected strong topics for a student."""
        if memory is None:
            return []
        topics = memory.get_strong_topics(student_id, subject_id)
        return [
            {
                "topic": t["topic"],
                "subject_id": t.get("subject_id"),
                "score": t.get("strength_score", 0.0),
            }
            for t in topics
        ]

    # ------------------------------------------------------------------
    # Mission progress
    # ------------------------------------------------------------------
    def compute_mission_progress(
        self,
        lessons_total: int,
        lessons_completed: int,
    ) -> Dict[str, Any]:
        """Compute progress toward a learning mission.

        Parameters
        ----------
        lessons_total:
            Total number of lessons in the mission.
        lessons_completed:
            Number of lessons completed.

        Returns
        -------
        dict
            Keys: ``progress_percent``, ``completed``, ``remaining``.
        """
        if lessons_total <= 0:
            return {
                "progress_percent": 0,
                "completed": False,
                "remaining": 0,
            }
        percent = round((lessons_completed / lessons_total) * 100)
        return {
            "progress_percent": min(100, max(0, percent)),
            "completed": lessons_completed >= lessons_total,
            "remaining": max(0, lessons_total - lessons_completed),
        }

    # ------------------------------------------------------------------
    # Progress analysis
    # ------------------------------------------------------------------
    def analyze_progress(
        self,
        student_id: int,
        memory: Memory,
    ) -> Dict[str, Any]:
        """Produce a holistic progress snapshot for a student.

        Parameters
        ----------
        student_id:
            The student.
        memory:
            Memory instance for reading topics and state.

        Returns
        -------
        dict
            Keys: ``weak_topics``, ``strong_topics``, ``current_state``.
        """
        return {
            "weak_topics": memory.get_weak_topics(student_id),
            "strong_topics": memory.get_strong_topics(student_id),
            "current_state": memory.get_state(student_id),
        }
