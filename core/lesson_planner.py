"""AI School OS — Phase 4.3 Lesson Planner.

Organizes a lesson into structured sections:

* Introduction
* Explanation
* Examples
* Exercises
* Reflection
* Next step

Pure logic — no AI calls, no database writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LessonSection:
    """A single section of a lesson plan.

    Attributes
    ----------
    name:
        Section identifier (e.g. ``"introduction"``).
    title:
        Human-readable section title.
    content:
        Section content/body text (filled in later by prompt builder).
    duration_minutes:
        Suggested duration in minutes.
    required:
        Whether this section is mandatory.
    """

    name: str
    title: str
    content: str = ""
    duration_minutes: int = 5
    required: bool = True


@dataclass
class LessonPlan:
    """A complete lesson plan.

    Attributes
    ----------
    sections:
        Ordered list of :class:`LessonSection` instances.
    total_duration_minutes:
        Sum of all section durations.
    difficulty:
        The difficulty level the plan targets.
    student_id:
        The student this plan is for.
    subject:
        The subject being taught.
    """

    sections: List[LessonSection] = field(default_factory=list)
    total_duration_minutes: int = 0
    difficulty: str = "medium"
    student_id: int = 0
    subject: str = ""

    def add_section(self, section: LessonSection) -> None:
        """Append a section and recompute total duration."""
        self.sections.append(section)
        self.total_duration_minutes += section.duration_minutes

    def get_section(self, name: str) -> Optional[LessonSection]:
        """Return a section by name, or ``None`` if not present."""
        for section in self.sections:
            if section.name == name:
                return section
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the lesson plan to a plain dict."""
        return {
            "sections": [
                {
                    "name": s.name,
                    "title": s.title,
                    "content": s.content,
                    "duration_minutes": s.duration_minutes,
                    "required": s.required,
                }
                for s in self.sections
            ],
            "total_duration_minutes": self.total_duration_minutes,
            "difficulty": self.difficulty,
            "student_id": self.student_id,
            "subject": self.subject,
        }


class LessonPlanner:
    """Builds a structured lesson plan for a student.

    The planner decides which sections to include and in what order,
    based on difficulty, teaching strategy, and student state.
    """

    # ------------------------------------------------------------------
    # Default section templates
    # ------------------------------------------------------------------
    _DEFAULT_SECTIONS = [
        ("introduction", "Introduction", 5, True),
        ("explanation", "Explanation", 10, True),
        ("examples", "Worked Examples", 8, True),
        ("exercises", "Practice Exercises", 10, True),
        ("reflection", "Reflection", 5, False),
        ("next_step", "Next Step", 3, True),
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def plan(
        self,
        student_id: int,
        subject: str,
        difficulty: str,
        strategy_name: str = "explain_first",
        topic: Optional[str] = None,
    ) -> LessonPlan:
        """Create a lesson plan.

        Parameters
        ----------
        student_id:
            The student the plan is for.
        subject:
            The subject being taught.
        difficulty:
            Assessed difficulty level.
        strategy_name:
            Name of the teaching strategy (used to adjust section
            weighting).
        topic:
            Optional specific topic within the subject.

        Returns
        -------
        LessonPlan
            The structured lesson plan.
        """
        plan = LessonPlan(
            sections=[],
            total_duration_minutes=0,
            difficulty=difficulty,
            student_id=student_id,
            subject=subject,
        )

        # Adjust durations based on difficulty.
        duration_multiplier = {
            "beginner": 1.2,
            "easy": 1.1,
            "medium": 1.0,
            "advanced": 0.9,
            "expert": 0.8,
        }.get(difficulty, 1.0)

        # Strategy-specific adjustments.
        skip_sections = self._sections_to_skip(strategy_name)

        for name, title, base_minutes, required in self._DEFAULT_SECTIONS:
            if name in skip_sections:
                continue
            minutes = max(1, int(base_minutes * duration_multiplier))
            section = LessonSection(
                name=name,
                title=title,
                duration_minutes=minutes,
                required=required,
            )
            # Inject topic context into content placeholder.
            if topic:
                section.content = f"Topic: {topic}"
            plan.add_section(section)

        return plan

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sections_to_skip(strategy_name: str) -> set[str]:
        """Return section names to skip for a given strategy."""
        if strategy_name == "practice_first":
            # Practice-first puts exercises before explanation.
            return {"reflection"}
        if strategy_name == "challenge":
            # Challenge mode skips gentle introduction.
            return {"introduction"}
        if strategy_name == "revision":
            # Revision skips reflection (covered by recap).
            return {"reflection"}
        return set()
