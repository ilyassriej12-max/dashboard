"""AI School OS — Phase 5.6 Competency Tracker.

Tracks competency mastery per student per subject.
Each competency stores a 0-100 mastery score.
Replaces the simple weak/strong topic tracking with a more granular
competency-based system.

All mastery data is persisted to SQLite via services/db/database.py
so it survives server restarts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.db.database import (
    load_all_competency_mastery,
    load_all_student_competency_mastery,
    save_competency_mastery,
)


@dataclass
class CompetencyMastery:
    """Mastery level for a single competency."""

    competency_id: str
    subject_id: str
    student_id: int
    score: float = 0.0  # 0-100
    updated_at: str = ""
    times_assessed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "competency_id": self.competency_id,
            "subject_id": self.subject_id,
            "student_id": self.student_id,
            "score": self.score,
            "updated_at": self.updated_at,
            "times_assessed": self.times_assessed,
        }


class CompetencyTracker:
    """Tracks competency mastery per student per subject.

    Replaces the simple weak/strong topic tracking with a more granular
    competency-based system where each competency has a 0-100 mastery score.

    All mastery data is kept in memory for fast access and persisted to
    SQLite so it survives server restarts.
    """

    def __init__(self) -> None:
        # student_id -> subject_id -> competency_id -> CompetencyMastery
        self._mastery: Dict[str, Dict[str, Dict[str, CompetencyMastery]]] = {}

    # ------------------------------------------------------------------
    # Database persistence
    # ------------------------------------------------------------------
    def load_for_student(self, student_id: int) -> None:
        """Load all competency mastery for a student from SQLite."""
        all_mastery = load_all_student_competency_mastery(student_id)
        student_key = str(student_id)
        self._mastery.setdefault(student_key, {})
        for subject_id, rows in all_mastery.items():
            self._mastery[student_key].setdefault(subject_id, {})
            for row in rows:
                cm = CompetencyMastery(
                    competency_id=row["competency_id"],
                    subject_id=subject_id,
                    student_id=student_id,
                    score=row["score"],
                    updated_at=str(row["updated_at"]) if row["updated_at"] else "",
                    times_assessed=row["times_assessed"],
                )
                self._mastery[student_key][subject_id][row["competency_id"]] = cm

    def _persist(
        self,
        student_id: int,
        subject_id: str,
        competency_id: str,
        cm: CompetencyMastery,
    ) -> None:
        """Persist a single competency mastery record to SQLite."""
        save_competency_mastery(
            student_id=student_id,
            subject_id=subject_id,
            competency_id=competency_id,
            score=cm.score,
            times_assessed=cm.times_assessed,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_mastery(
        self,
        student_id: int,
        subject_id: str,
        competency_id: str,
    ) -> Optional[CompetencyMastery]:
        """Get mastery for a specific competency."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        subject_mastery = student_mastery.get(subject_id, {})
        return subject_mastery.get(competency_id)

    def get_all_mastery(
        self,
        student_id: int,
        subject_id: str,
    ) -> Dict[str, CompetencyMastery]:
        """Get all competency mastery for a student in a subject."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        return student_mastery.get(subject_id, {})

    def get_all_student_mastery(
        self,
        student_id: int,
    ) -> Dict[str, Dict[str, CompetencyMastery]]:
        """Get all competency mastery for a student across all subjects."""
        self.load_for_student(student_id)
        return self._mastery.get(str(student_id), {})

    def update_mastery(
        self,
        student_id: int,
        subject_id: str,
        competency_id: str,
        score: float,
    ) -> CompetencyMastery:
        """Update mastery score for a competency and persist to SQLite.

        Score is clamped to 0-100. Uses a weighted average with previous
        score to smooth out fluctuations.
        """
        self.load_for_student(student_id)
        student_mastery = self._mastery.setdefault(str(student_id), {})
        subject_mastery = student_mastery.setdefault(subject_id, {})

        existing = subject_mastery.get(competency_id)
        if existing is None:
            existing = CompetencyMastery(
                competency_id=competency_id,
                subject_id=subject_id,
                student_id=student_id,
                score=0.0,
            )
            subject_mastery[competency_id] = existing

        # Weighted average: new score counts 60%, existing 40%
        existing.score = round(existing.score * 0.4 + score * 0.6, 1)
        existing.score = max(0.0, min(100.0, existing.score))
        existing.times_assessed += 1

        import time as _time
        now = str(int(_time.time() * 1000))
        existing.updated_at = now

        self._persist(student_id, subject_id, competency_id, existing)
        return existing

    def is_mastered(
        self,
        student_id: int,
        subject_id: str,
        competency_id: str,
        threshold: float = 70.0,
    ) -> bool:
        """Check if a competency is mastered (score >= threshold)."""
        mastery = self.get_mastery(student_id, subject_id, competency_id)
        if mastery is None:
            return False
        return mastery.score >= threshold

    def get_weak_competencies(
        self,
        student_id: int,
        subject_id: str,
        threshold: float = 70.0,
    ) -> List[CompetencyMastery]:
        """Get competencies below the threshold."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        subject_mastery = student_mastery.get(subject_id, {})
        return [
            m for m in subject_mastery.values()
            if m.score < threshold
        ]

    def get_strong_competencies(
        self,
        student_id: int,
        subject_id: str,
        threshold: float = 70.0,
    ) -> List[CompetencyMastery]:
        """Get competencies at or above the threshold."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        subject_mastery = student_mastery.get(subject_id, {})
        return [
            m for m in subject_mastery.values()
            if m.score >= threshold
        ]

    def get_all_weak_competencies(
        self,
        student_id: int,
        threshold: float = 70.0,
    ) -> Dict[str, List[CompetencyMastery]]:
        """Get all weak competencies across all subjects for a student."""
        self.load_for_student(student_id)
        result: Dict[str, List[CompetencyMastery]] = {}
        student_mastery = self._mastery.get(str(student_id), {})
        for subject_id, subject_mastery in student_mastery.items():
            weak = [m for m in subject_mastery.values() if m.score < threshold]
            if weak:
                result[subject_id] = weak
        return result

    def get_all_strong_competencies(
        self,
        student_id: int,
        threshold: float = 70.0,
    ) -> Dict[str, List[CompetencyMastery]]:
        """Get all strong competencies across all subjects for a student."""
        self.load_for_student(student_id)
        result: Dict[str, List[CompetencyMastery]] = {}
        student_mastery = self._mastery.get(str(student_id), {})
        for subject_id, subject_mastery in student_mastery.items():
            strong = [m for m in subject_mastery.values() if m.score >= threshold]
            if strong:
                result[subject_id] = strong
        return result

    def get_average_mastery(
        self,
        student_id: int,
        subject_id: str,
    ) -> float:
        """Get average mastery score across all competencies for a subject."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        subject_mastery = student_mastery.get(subject_id, {})
        if not subject_mastery:
            return 0.0
        scores = [m.score for m in subject_mastery.values()]
        return round(sum(scores) / len(scores), 1)

    def get_overall_mastery(
        self,
        student_id: int,
    ) -> float:
        """Get overall mastery across all subjects."""
        self.load_for_student(student_id)
        student_mastery = self._mastery.get(str(student_id), {})
        all_scores: List[float] = []
        for subject_mastery in student_mastery.values():
            all_scores.extend(m.score for m in subject_mastery.values())
        if not all_scores:
            return 0.0
        return round(sum(all_scores) / len(all_scores), 1)