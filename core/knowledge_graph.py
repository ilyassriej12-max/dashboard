"""AI School OS — Phase 5.4 Knowledge Graph.

Tracks dependencies between chapters and lessons.
Students cannot progress to a chapter if prerequisite mastery is insufficient.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set


class KnowledgeGraph:
    """Manages prerequisite relationships between chapters and lessons.

    A chapter can only be started if all prerequisite chapters have been
    mastered (mastery score >= threshold). This ensures students build
    foundational knowledge before advancing.
    """

    def __init__(self) -> None:
        # chapter_id -> set of prerequisite chapter_ids
        self._chapter_prereqs: Dict[str, Set[str]] = {}
        # lesson_id -> set of prerequisite lesson_ids
        self._lesson_prereqs: Dict[str, Set[str]] = {}
        # chapter_id -> set of chapter_ids that depend on it (reverse)
        self._chapter_dependents: Dict[str, Set[str]] = {}
        # lesson_id -> set of lesson_ids that depend on it (reverse)
        self._lesson_dependents: Dict[str, Set[str]] = {}

    def add_chapter_prerequisite(
        self,
        chapter_id: str,
        prerequisite_id: str,
    ) -> None:
        """Add a prerequisite relationship between chapters."""
        if chapter_id not in self._chapter_prereqs:
            self._chapter_prereqs[chapter_id] = set()
        self._chapter_prereqs[chapter_id].add(prerequisite_id)

        if prerequisite_id not in self._chapter_dependents:
            self._chapter_dependents[prerequisite_id] = set()
        self._chapter_dependents[prerequisite_id].add(chapter_id)

    def add_lesson_prerequisite(
        self,
        lesson_id: str,
        prerequisite_id: str,
    ) -> None:
        """Add a prerequisite relationship between lessons."""
        if lesson_id not in self._lesson_prereqs:
            self._lesson_prereqs[lesson_id] = set()
        self._lesson_prereqs[lesson_id].add(prerequisite_id)

        if prerequisite_id not in self._lesson_dependents:
            self._lesson_dependents[prerequisite_id] = set()
        self._lesson_dependents[prerequisite_id].add(lesson_id)

    def get_prerequisites(self, chapter_id: str) -> Set[str]:
        """Get all prerequisite chapter IDs for a chapter."""
        return self._chapter_prereqs.get(chapter_id, set()).copy()

    def get_lesson_prerequisites(self, lesson_id: str) -> Set[str]:
        """Get all prerequisite lesson IDs for a lesson."""
        return self._lesson_prereqs.get(lesson_id, set()).copy()

    def get_dependents(self, chapter_id: str) -> Set[str]:
        """Get all chapters that depend on this chapter."""
        return self._chapter_dependents.get(chapter_id, set()).copy()

    def is_prerequisite_met(
        self,
        chapter_id: str,
        completed_chapters: Set[str],
        mastery_threshold: float = 70.0,
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Check if all prerequisites for a chapter are met.

        A prerequisite is met if the chapter is completed AND mastery
        meets the threshold (if mastery scores are provided).
        """
        prereqs = self._chapter_prereqs.get(chapter_id, set())
        if not prereqs:
            return True

        for prereq_id in prereqs:
            if prereq_id not in completed_chapters:
                return False
            # If mastery scores are provided, check mastery threshold
            if mastery_scores is not None:
                mastery = mastery_scores.get(prereq_id, 0.0)
                if mastery < mastery_threshold:
                    return False

        return True

    def get_blocking_prerequisites(
        self,
        chapter_id: str,
        completed_chapters: Set[str],
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> List[str]:
        """Get list of prerequisite chapter IDs that block progress."""
        prereqs = self._chapter_prereqs.get(chapter_id, set())
        blocking: List[str] = []
        for prereq_id in prereqs:
            if prereq_id not in completed_chapters:
                blocking.append(prereq_id)
            elif mastery_scores is not None:
                mastery = mastery_scores.get(prereq_id, 0.0)
                if mastery < 70.0:
                    blocking.append(prereq_id)
        return blocking

    def can_start_lesson(
        self,
        lesson_id: str,
        completed_lessons: Set[str],
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Check if a lesson can be started."""
        prereqs = self._lesson_prereqs.get(lesson_id, set())
        if not prereqs:
            return True

        for prereq_id in prereqs:
            if prereq_id not in completed_lessons:
                return False
            if mastery_scores is not None:
                mastery = mastery_scores.get(prereq_id, 0.0)
                if mastery < 70.0:
                    return False

        return True

    def get_blocking_lesson_prerequisites(
        self,
        lesson_id: str,
        completed_lessons: Set[str],
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> List[str]:
        """Get list of lesson prerequisite IDs that block progress."""
        prereqs = self._lesson_prereqs.get(lesson_id, set())
        blocking: List[str] = []
        for prereq_id in prereqs:
            if prereq_id not in completed_lessons:
                blocking.append(prereq_id)
            elif mastery_scores is not None:
                mastery = mastery_scores.get(prereq_id, 0.0)
                if mastery < 70.0:
                    blocking.append(prereq_id)
        return blocking