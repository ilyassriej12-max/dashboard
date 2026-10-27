"""AI School OS — Phase 5.4 Curriculum Engine.

Loads curriculum data from teacher plugin directories (config.json)
and provides curriculum-aware queries for the teaching pipeline.

Each teacher plugin folder contains:
    config.json — may contain a ``curriculum`` key that is either a
    simple list of chapter titles or an object with ``chapters``,
    ``competencies``, and ``objectives``.
    persona.md      — teacher personality text

The CurriculumEngine loads all curricula on startup and provides methods
to query curriculum data for any subject.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class Chapter:
    """A chapter within a subject curriculum."""

    def __init__(
        self,
        chapter_id: str,
        title: str,
        subject: str,
        description: str = "",
        lessons: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        competencies: Optional[List[str]] = None,
        objectives: Optional[List[str]] = None,
        estimated_duration_minutes: int = 0,
        difficulty: str = "beginner",
        order: int = 0,
    ) -> None:
        self.chapter_id = chapter_id
        self.title = title
        self.subject = subject
        self.description = description
        self.lessons = lessons or []
        self.prerequisites = prerequisites or []
        self.competencies = competencies or []
        self.objectives = objectives or []
        self.estimated_duration_minutes = estimated_duration_minutes
        self.difficulty = difficulty
        self.order = order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "title": self.title,
            "subject": self.subject,
            "description": self.description,
            "lessons": self.lessons,
            "prerequisites": self.prerequisites,
            "competencies": self.competencies,
            "objectives": self.objectives,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty": self.difficulty,
            "order": self.order,
        }


class Lesson:
    """A single lesson within a chapter."""

    def __init__(
        self,
        lesson_id: str,
        title: str,
        chapter_id: str,
        subject: str,
        description: str = "",
        content: str = "",
        key_concepts: Optional[List[str]] = None,
        learning_objectives: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        estimated_duration_minutes: int = 0,
        difficulty: str = "beginner",
        order: int = 0,
    ) -> None:
        self.lesson_id = lesson_id
        self.title = title
        self.chapter_id = chapter_id
        self.subject = subject
        self.description = description
        self.content = content
        self.key_concepts = key_concepts or []
        self.learning_objectives = learning_objectives or []
        self.prerequisites = prerequisites or []
        self.estimated_duration_minutes = estimated_duration_minutes
        self.difficulty = difficulty
        self.order = order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lesson_id": self.lesson_id,
            "title": self.title,
            "chapter_id": self.chapter_id,
            "subject": self.subject,
            "description": self.description,
            "content": self.content,
            "key_concepts": self.key_concepts,
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty": self.difficulty,
            "order": self.order,
        }


class Competency:
    """A competency within a subject curriculum."""

    def __init__(
        self,
        id: str,
        name: str,
        subject: str,
        chapter_id: str,
        description: str = "",
        mastery_threshold: int = 70,
        prerequisite_competencies: Optional[List[str]] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.subject = subject
        self.chapter_id = chapter_id
        self.description = description
        self.mastery_threshold = mastery_threshold
        self.prerequisite_competencies = prerequisite_competencies or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "chapter_id": self.chapter_id,
            "description": self.description,
            "mastery_threshold": self.mastery_threshold,
            "prerequisite_competencies": self.prerequisite_competencies,
        }


class CurriculumEngine:
    """Loads and manages curriculum data from teacher plugin directories.

    Each teacher plugin folder contains:
      config.json — may contain a ``curriculum`` key that is either a
      simple list of chapter titles or an object with ``chapters``,
      ``competencies``, and ``objectives``.
      persona.md      — teacher personality text

    The CurriculumEngine loads all curricula on startup and provides methods
    to query curriculum data for any subject.
    """

    def __init__(self, teachers_dir: str = "teachers") -> None:
        self.teachers_dir = Path(teachers_dir)
        self._curricula: Dict[str, Dict[str, Any]] = {}
        self._chapters: Dict[str, Chapter] = {}
        self._lessons: Dict[str, Lesson] = {}
        self._competencies: Dict[str, Competency] = {}
        self._subject_teachers: Dict[str, str] = {}
        self._teacher_subjects: Dict[str, str] = {}

    def load_all(self) -> None:
        """Load all curriculum data from the teachers directory."""
        self._curricula.clear()
        self._chapters.clear()
        self._lessons.clear()
        self._competencies.clear()
        self._subject_teachers.clear()
        self._teacher_subjects.clear()

        if not self.teachers_dir.is_dir():
            return

        for teacher_dir in sorted(self.teachers_dir.iterdir()):
            if not teacher_dir.is_dir():
                continue

            config_path = teacher_dir / "config.json"
            if not config_path.is_file():
                continue

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                continue

            teacher_id = teacher_dir.name
            subject = config.get("subject", teacher_dir.name)
            curriculum_data = {
                "teacher_id": teacher_id,
                "subject": subject,
                "name": config.get("name", subject),
                "description": config.get("description", ""),
                "model": config.get("model", ""),
                "priority": config.get("priority", 0),
                "allowed_tools": config.get("allowed_tools", []),
                "chapters": [],
                "lessons": [],
                "competencies": [],
                "objectives": config.get("objectives", []),
                "estimated_duration_minutes": config.get(
                    "estimated_duration_minutes", 0
                ),
                "difficulty": config.get("difficulty_preference", "beginner"),
            }

            # Load curriculum from config.json.  The ``curriculum`` key may be
            # a simple list of chapter titles (math) or an object with
            # chapters, competencies, objectives (other teachers).
            curriculum_raw = config.get("curriculum")
            chapters_raw: List[Dict[str, Any]] = []
            competencies_raw: List[Dict[str, Any]] = []
            objectives_raw: List[str] = []

            if isinstance(curriculum_raw, dict):
                chapters_raw = curriculum_raw.get("chapters", [])
                competencies_raw = curriculum_raw.get("competencies", [])
                objectives_raw = curriculum_raw.get("objectives", [])
            elif isinstance(curriculum_raw, list):
                # Build minimal chapter entries from the title list.
                for idx, title in enumerate(curriculum_raw):
                    chapters_raw.append(
                        {
                            "chapter_id": f"{subject.lower()}_ch_{idx+1}",
                            "title": title,
                            "lessons": [],
                            "prerequisites": [],
                            "competencies": [],
                            "objectives": [],
                            "order": idx + 1,
                        }
                    )

            # Load chapters (and their nested lessons).
            for ch_data in chapters_raw:
                chapter = Chapter(
                    chapter_id=ch_data.get("chapter_id", ch_data.get("id", "")),
                    title=ch_data.get("title", ""),
                    subject=subject,
                    description=ch_data.get("description", ""),
                    lessons=ch_data.get("lessons", []),
                    prerequisites=ch_data.get("prerequisites", []),
                    competencies=ch_data.get("competencies", []),
                    objectives=ch_data.get("objectives", []),
                    estimated_duration_minutes=ch_data.get(
                        "estimated_duration_minutes", 0
                    ),
                    difficulty=ch_data.get("difficulty", "beginner"),
                    order=ch_data.get("order", 0),
                )
                curriculum_data["chapters"].append(chapter.chapter_id)
                self._chapters[chapter.chapter_id] = chapter

                # Extract nested lessons from each chapter.
                lesson_ids = []
                for lesson_data in chapter.lessons if isinstance(chapter.lessons, list) else []:
                    if isinstance(lesson_data, dict):
                        lesson = Lesson(
                            lesson_id=lesson_data.get(
                                "lesson_id", lesson_data.get("id", "")
                            ),
                            title=lesson_data.get("title", ""),
                            subject=subject,
                            chapter_id=chapter.chapter_id,
                            description=lesson_data.get("description", ""),
                            content=lesson_data.get("content", ""),
                            key_concepts=lesson_data.get("key_concepts", []),
                            learning_objectives=lesson_data.get(
                                "learning_objectives", []
                            ),
                            prerequisites=lesson_data.get("prerequisites", []),
                            estimated_duration_minutes=lesson_data.get(
                                "estimated_duration_minutes", 0
                            ),
                            difficulty=lesson_data.get("difficulty", "beginner"),
                            order=lesson_data.get("order", 0),
                        )
                        lesson_ids.append(lesson.lesson_id)
                        self._lessons[lesson.lesson_id] = lesson
                # Replace chapter.lessons (list of dicts) with list of lesson ID strings.
                chapter.lessons = lesson_ids
                curriculum_data["lessons"].extend(lesson_ids)

            # Load competencies (from curriculum object or chapter-level).
            for comp_data in competencies_raw:
                if isinstance(comp_data, dict):
                    comp = Competency(
                        id=comp_data.get("id", comp_data.get("name", "")),
                        name=comp_data.get("name", ""),
                        subject=subject,
                        chapter_id=comp_data.get("chapter_id", ""),
                        description=comp_data.get("description", ""),
                        mastery_threshold=comp_data.get(
                            "mastery_threshold", 75
                        ),
                        prerequisite_competencies=comp_data.get(
                            "prerequisite_competencies", []
                        ),
                    )
                    curriculum_data["competencies"].append(comp.id)
                    self._competencies[comp.id] = comp

            # Also pull competencies from within chapters.
            for ch_data in chapters_raw:
                for comp_data in ch_data.get("competencies", []):
                    if isinstance(comp_data, dict):
                        comp_id = comp_data.get("id", comp_data.get("name", ""))
                        if comp_id not in self._competencies:
                            comp = Competency(
                                id=comp_id,
                                name=comp_data.get("name", ""),
                                subject=subject,
                                chapter_id=ch_data.get("chapter_id", ch_data.get("id", "")),
                                description=comp_data.get("description", ""),
                                mastery_threshold=comp_data.get(
                                    "mastery_threshold", 75
                                ),
                                prerequisite_competencies=comp_data.get(
                                    "prerequisite_competencies", []
                                ),
                            )
                            curriculum_data["competencies"].append(comp.id)
                            self._competencies[comp.id] = comp

            # Objectives from curriculum object.
            for obj in objectives_raw:
                if obj not in curriculum_data["objectives"]:
                    curriculum_data["objectives"].append(obj)

            self._curricula[subject] = curriculum_data
            self._subject_teachers[subject] = teacher_id
            self._teacher_subjects[teacher_id] = subject

    def get_curriculum(self, subject: str) -> Optional[Dict[str, Any]]:
        """Get the curriculum data for a subject."""
        return self._curricula.get(subject)

    def get_chapter(self, chapter_id: str) -> Optional[Chapter]:
        """Get a chapter by ID."""
        return self._chapters.get(chapter_id)

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """Get a lesson by ID."""
        return self._lessons.get(lesson_id)

    def get_competency(self, competency_id: str) -> Optional[Competency]:
        """Get a competency by ID."""
        return self._competencies.get(competency_id)

    def get_subject_for_teacher(self, teacher_id: str) -> Optional[str]:
        """Get the subject taught by a teacher."""
        return self._teacher_subjects.get(teacher_id)

    def get_teacher_for_subject(self, subject: str) -> Optional[str]:
        """Get the teacher ID for a subject."""
        return self._subject_teachers.get(subject)

    def get_all_subjects(self) -> List[str]:
        """Get all subject IDs."""
        return list(self._curricula.keys())

    def get_all_teachers(self) -> List[str]:
        """Get all teacher IDs."""
        return list(self._teacher_subjects.keys())

    def get_prerequisites(self, chapter_id: str) -> List[str]:
        """Get prerequisite chapter IDs for a chapter."""
        chapter = self._chapters.get(chapter_id)
        if chapter:
            return chapter.prerequisites
        return []

    def get_competencies_for_chapter(self, chapter_id: str) -> List[str]:
        """Get competency IDs for a chapter."""
        chapter = self._chapters.get(chapter_id)
        if chapter:
            return chapter.competencies
        return []

    def get_objectives_for_chapter(self, chapter_id: str) -> List[str]:
        """Get objective descriptions for a chapter."""
        chapter = self._chapters.get(chapter_id)
        if chapter:
            return chapter.objectives
        return []

    def is_prerequisite_met(
        self,
        chapter_id: str,
        completed_chapters: Set[str],
    ) -> bool:
        """Check if all prerequisites for a chapter are met."""
        chapter = self._chapters.get(chapter_id)
        if not chapter:
            return True
        return all(
            prereq in completed_chapters for prereq in chapter.prerequisites
        )

    def get_next_lesson(
        self,
        student_id: int,
        subject_id: str,
        completed_lessons: List[str],
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> Optional[str]:
        """Get the next lesson for a student in a subject.

        Returns the first uncompleted lesson whose prerequisites are met.
        """
        curriculum = self._curricula.get(subject_id)
        if not curriculum:
            return None

        completed = set(completed_lessons)
        for lesson_id in curriculum["lessons"]:
            if lesson_id not in completed:
                lesson = self._lessons.get(lesson_id)
                if lesson:
                    prereqs = lesson.prerequisites
                    if all(p in completed for p in prereqs):
                        return lesson_id
        return None