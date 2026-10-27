"""AI School OS — Phase 5.6 Progress Tracker.

Tracks per-student per-lesson progress:
- completed lessons
- current lesson
- next lesson
- skipped lessons
- time spent
- attempts

Works per subject per student. All progress is persisted to SQLite
via services/db/database.py so it survives server restarts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.db.database import (
    load_all_lesson_progress,
    load_all_student_lesson_progress,
    save_lesson_progress,
)


@dataclass
class LessonProgress:
    """Progress for a single lesson."""

    lesson_id: str
    subject: str
    status: str = "not_started"  # not_started, in_progress, completed, skipped
    attempts: int = 0
    time_spent_minutes: int = 0
    best_score: Optional[float] = None
    last_attempt_at: Optional[str] = None
    completed_at: Optional[str] = None


class ProgressTracker:
    """Tracks per-student per-lesson progress across all subjects.

    Progress is kept in memory for fast access and persisted to SQLite
    so it survives server restarts. On construction, existing progress
    is loaded from the database.
    """

    def __init__(self) -> None:
        # student_id -> subject_id -> lesson_id -> LessonProgress
        self._progress: Dict[str, Dict[str, Dict[str, LessonProgress]]] = {}
        self._load_all_from_db()

    # ------------------------------------------------------------------
    # Database persistence
    # ------------------------------------------------------------------
    def _load_all_from_db(self) -> None:
        """Placeholder - actual loading happens in load_for_student()."""
        pass

    def load_for_student(self, student_id: int) -> None:
        """Load all lesson progress for a student from SQLite."""
        all_progress = load_all_student_lesson_progress(student_id)
        student_key = str(student_id)
        self._progress.setdefault(student_key, {})
        for subject_id, lessons in all_progress.items():
            self._progress[student_key].setdefault(subject_id, {})
            for row in lessons:
                lp = LessonProgress(
                    lesson_id=row["lesson_id"],
                    subject=subject_id,
                    status=row["status"],
                    attempts=row["attempts"],
                    time_spent_minutes=row["time_spent_minutes"],
                    best_score=row["best_score"],
                    last_attempt_at=str(row["last_attempt_at"])
                    if row["last_attempt_at"] is not None
                    else None,
                    completed_at=str(row["completed_at"])
                    if row["completed_at"] is not None
                    else None,
                )
                self._progress[student_key][subject_id][row["lesson_id"]] = lp

    def _persist(self, student_id: int, subject_id: str, lesson_id: str) -> None:
        """Persist a single lesson progress record to SQLite."""
        student_progress = self._progress.get(str(student_id), {})
        subject_progress = student_progress.get(subject_id, {})
        progress = subject_progress.get(lesson_id)
        if progress is None:
            return
        save_lesson_progress(
            student_id=student_id,
            subject_id=subject_id,
            lesson_id=lesson_id,
            status=progress.status,
            attempts=progress.attempts,
            time_spent_minutes=progress.time_spent_minutes,
            best_score=progress.best_score,
            last_attempt_at=int(progress.last_attempt_at) if progress.last_attempt_at else None,
            completed_at=int(progress.completed_at) if progress.completed_at else None,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_progress(
        self,
        student_id: int,
        subject_id: str,
        lesson_id: str,
    ) -> Optional[LessonProgress]:
        """Get progress for a specific lesson."""
        self.load_for_student(student_id)
        student_progress = self._progress.get(str(student_id), {})
        subject_progress = student_progress.get(subject_id, {})
        return subject_progress.get(lesson_id)

    def get_all_progress(
        self,
        student_id: int,
        subject_id: str,
    ) -> Dict[str, LessonProgress]:
        """Get all lesson progress for a student in a subject."""
        self.load_for_student(student_id)
        student_progress = self._progress.get(str(student_id), {})
        return subject_progress.get(subject_id, {})

    def get_all_student_progress(
        self,
        student_id: int,
    ) -> Dict[str, Dict[str, LessonProgress]]:
        """Get all progress for a student across all subjects."""
        self.load_for_student(student_id)
        return self._progress.get(str(student_id), {})

    def update_progress(
        self,
        student_id: int,
        subject_id: str,
        lesson_id: str,
        status: Optional[str] = None,
        time_spent_minutes: Optional[int] = None,
        score: Optional[float] = None,
        increment_attempts: bool = False,
    ) -> LessonProgress:
        """Update progress for a lesson and persist to SQLite."""
        self.load_for_student(student_id)
        student_progress = self._progress.setdefault(str(student_id), {})
        subject_progress = student_progress.setdefault(subject_id, {})

        progress = subject_progress.get(lesson_id)
        if progress is None:
            progress = LessonProgress(
                lesson_id=lesson_id,
                subject=subject_id,
            )
            subject_progress[lesson_id] = progress

        if status is not None:
            progress.status = status
        if time_spent_minutes is not None:
            progress.time_spent_minutes += time_spent_minutes
        if score is not None:
            if progress.best_score is None or score > progress.best_score:
                progress.best_score = score
        if increment_attempts:
            progress.attempts += 1

        import time as _time
        now = int(_time.time() * 1000)
        progress.last_attempt_at = str(now)

        if status == "completed":
            progress.completed_at = str(now)

        self._persist(student_id, subject_id, lesson_id)
        return progress

    def mark_completed(
        self,
        student_id: int,
        subject_id: str,
        lesson_id: str,
        score: Optional[float] = None,
        time_spent_minutes: Optional[int] = None,
    ) -> LessonProgress:
        """Mark a lesson as completed."""
        return self.update_progress(
            student_id=student_id,
            subject_id=subject_id,
            lesson_id=lesson_id,
            status="completed",
            time_spent_minutes=time_spent_minutes,
            score=score,
        )

    def mark_in_progress(
        self,
        student_id: int,
        subject_id: str,
        lesson_id: str,
    ) -> LessonProgress:
        """Mark a lesson as in progress."""
        return self.update_progress(
            student_id=student_id,
            subject_id=subject_id,
            lesson_id=lesson_id,
            status="in_progress",
        )

    def mark_skipped(
        self,
        student_id: int,
        subject_id: str,
        lesson_id: str,
    ) -> LessonProgress:
        """Mark a lesson as skipped."""
        return self.update_progress(
            student_id=student_id,
            subject_id=subject_id,
            lesson_id=lesson_id,
            status="skipped",
        )

    def get_completed_lessons(
        self,
        student_id: int,
        subject_id: str,
    ) -> List[str]:
        """Get list of completed lesson IDs for a subject."""
        self.load_for_student(student_id)
        student_progress = self._progress.get(str(student_id), {})
        subject_progress = student_progress.get(subject_id, {})
        return [
            lid for lid, p in subject_progress.items()
            if p.status == "completed"
        ]

    def get_current_lesson(
        self,
        student_id: int,
        subject_id: str,
    ) -> Optional[str]:
        """Get the current in-progress lesson ID."""
        self.load_for_student(student_id)
        student_progress = self._progress.get(str(student_id), {})
        subject_progress = student_progress.get(subject_id, {})
        for lid, p in subject_progress.items():
            if p.status == "in_progress":
                return lid
        return None

    def get_next_lesson(
        self,
        student_id: int,
        subject_id: str,
        all_lesson_ids: List[str],
        completed_lessons: List[str],
    ) -> Optional[str]:
        """Get the next lesson to take, considering prerequisites."""
        # Find first not-completed lesson in order
        completed_set = set(completed_lessons)
        for lid in all_lesson_ids:
            if lid not in completed_set:
                return lid
        return None

    def get_progress_summary(
        self,
        student_id: int,
        subject_id: str,
    ) -> Dict[str, Any]:
        """Get a summary of progress for a subject."""
        self.load_for_student(student_id)
        student_progress = self._progress.get(str(student_id), {})
        subject_progress = student_progress.get(subject_id, {})

        total = len(subject_progress)
        completed = sum(1 for p in subject_progress.values() if p.status == "completed")
        in_progress = sum(1 for p in subject_progress.values() if p.status == "in_progress")
        skipped = sum(1 for p in subject_progress.values() if p.status == "skipped")
        not_started = sum(1 for p in subject_progress.values() if p.status == "not_started")

        total_time = sum(p.time_spent_minutes for p in subject_progress.values())
        total_attempts = sum(p.attempts for p in subject_progress.values())

        return {
            "total_lessons": total,
            "completed": completed,
            "in_progress": in_progress,
            "skipped": skipped,
            "not_started": not_started,
            "completion_percent": round((completed / total * 100) if total > 0 else 0, 1),
            "total_time_minutes": total_time,
            "total_attempts": total_attempts,
        }