"""AI School OS — Phase 4.1 abstract Teacher class.

Every teacher in future phases must inherit from :class:`Teacher`.
This class defines the *shape* of a teacher — identity, capabilities,
and behaviour contracts — without implementing any AI generation.

Responsibilities:

* teacher id, subject, display name, description
* supported curriculum and tools
* model preference
* explanation style, reasoning style, vocabulary, examples
* preferred lesson flow, correction style, teaching personality
* objectives, restrictions, keywords, difficulty preference
* :meth:`ask` — process a student message
* :meth:`prepare_context` — assemble teacher-specific context
* :meth:`available_tools` — list supported tool names

No LLM calls happen here.  All methods return placeholders.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class Teacher(ABC):
    """Abstract base class for all AI School OS teachers.

    Subclasses must provide concrete values for the identity attributes
    and implement :meth:`ask`, :meth:`prepare_context`, and
    :meth:`available_tools`.
    """

    # ------------------------------------------------------------------
    # Identity (set by subclasses via __init__)
    # ------------------------------------------------------------------
    teacher_id: str
    """Unique identifier for this teacher."""

    subject: str
    """Subject this teacher teaches (e.g. ``"Mathematics"``)."""

    display_name: str
    """Human-readable name shown in the UI."""

    description: str
    """Short description of the teacher's approach/personality."""

    supported_curriculum: List[str]
    """List of curriculum topics this teacher can cover."""

    supported_tools: List[str]
    """List of tool names this teacher can use (e.g. ``"whiteboard"``)."""

    model_preference: Optional[str]
    """Preferred AI model identifier, or ``None`` for default."""

    # ------------------------------------------------------------------
    # Teaching intelligence attributes (Phase 5.1)
    # ------------------------------------------------------------------
    explanation_style: str
    """How this teacher explains concepts (e.g. "step-by-step", "concept-first")."""

    reasoning_style: str
    """How this teacher reasons through problems (e.g. "deductive", "inductive")."""

    vocabulary: List[str]
    """Preferred vocabulary terms this teacher uses."""

    examples: List[str]
    """Example topics this teacher commonly uses."""

    preferred_lesson_flow: List[str]
    """Preferred order of lesson sections."""

    correction_style: str
    """How this teacher corrects mistakes (e.g. "gentle", "direct")."""

    teaching_personality: str
    """The teacher's personality archetype."""

    objectives: List[str]
    """Learning objectives this teacher focuses on."""

    restrictions: List[str]
    """Topics or approaches this teacher avoids."""

    keywords: List[str]
    """Keywords this teacher responds to for routing."""

    difficulty_preference: str
    """Preferred starting difficulty (e.g. "beginner", "intermediate")."""

    # ------------------------------------------------------------------
    # Curriculum data (Phase 5.4)
    # ------------------------------------------------------------------
    curriculum_data: Dict[str, Any]
    """Full curriculum data loaded from curriculum.json."""
    chapters: List[Dict[str, Any]]
    """List of chapter dicts."""
    lessons: List[Dict[str, Any]]
    """List of lesson dicts."""
    competencies: List[Dict[str, Any]]
    """List of competency dicts."""

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def __init__(
        self,
        teacher_id: str,
        subject: str,
        display_name: str,
        description: str = "",
        supported_curriculum: Optional[List[str]] = None,
        supported_tools: Optional[List[str]] = None,
        model_preference: Optional[str] = None,
        explanation_style: str = "balanced",
        reasoning_style: str = "direct",
        vocabulary: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        preferred_lesson_flow: Optional[List[str]] = None,
        correction_style: str = "gentle",
        teaching_personality: str = "encouraging",
        objectives: Optional[List[str]] = None,
        restrictions: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        difficulty_preference: str = "beginner",
        curriculum_data: Optional[Dict[str, Any]] = None,
        chapters: Optional[List[Dict[str, Any]]] = None,
        lessons: Optional[List[Dict[str, Any]]] = None,
        competencies: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.teacher_id = teacher_id
        self.subject = subject
        self.display_name = display_name
        self.description = description
        self.supported_curriculum = supported_curriculum or []
        self.supported_tools = supported_tools or []
        self.model_preference = model_preference
        self.explanation_style = explanation_style
        self.reasoning_style = reasoning_style
        self.vocabulary = vocabulary or []
        self.examples = examples or []
        self.preferred_lesson_flow = preferred_lesson_flow or []
        self.correction_style = correction_style
        self.teaching_personality = teaching_personality
        self.objectives = objectives or []
        self.restrictions = restrictions or []
        self.keywords = keywords or []
        self.difficulty_preference = difficulty_preference
        self.curriculum_data = curriculum_data or {}
        self.chapters = chapters or []
        self.lessons = lessons or []
        self.competencies = competencies or []

    # ------------------------------------------------------------------
    # Intelligence accessors
    # ------------------------------------------------------------------
    def get_explanation_style(self) -> str:
        """Return this teacher's explanation style."""
        return self.explanation_style

    def get_reasoning_style(self) -> str:
        """Return this teacher's reasoning style."""
        return self.reasoning_style

    def get_vocabulary(self) -> List[str]:
        """Return preferred vocabulary terms."""
        return self.vocabulary

    def get_examples(self) -> List[str]:
        """Return example topics this teacher uses."""
        return self.examples

    def get_preferred_lesson_flow(self) -> List[str]:
        """Return preferred lesson section order."""
        return self.preferred_lesson_flow

    def get_correction_style(self) -> str:
        """Return how this teacher corrects mistakes."""
        return self.correction_style

    def get_teaching_personality(self) -> str:
        """Return the teacher's personality archetype."""
        return self.teaching_personality

    def get_objectives(self) -> List[str]:
        """Return learning objectives this teacher focuses on."""
        return self.objectives

    def get_restrictions(self) -> List[str]:
        """Return topics or approaches this teacher avoids."""
        return self.restrictions

    def get_keywords(self) -> List[str]:
        """Return keywords this teacher responds to for routing."""
        return self.keywords

    def get_difficulty_preference(self) -> str:
        """Return the preferred starting difficulty."""
        return self.difficulty_preference

    # ------------------------------------------------------------------
    # Teacher calling interface (Phase 5.1 preparation)
    # ------------------------------------------------------------------
    def request_teacher(self, teacher_id: str) -> Optional[str]:
        """Request another teacher to handle this request.

        Returns the teacher_id of the requested teacher, or ``None`` if
        this teacher does not request a handoff.  This does *not*
        execute a multi-teacher conversation — it only prepares the
        routing information for future phases.
        """
        return None

    # ------------------------------------------------------------------
    # Behaviour contracts (implemented by subclasses, placeholders only)
    # ------------------------------------------------------------------
    @abstractmethod
    async def ask(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a student message and return a response.

        Parameters
        ----------
        message:
            The student's input text.
        context:
            Optional assembled context (memory, curriculum, router,
            provider, etc.).

        Returns
        -------
        dict
            A response dict with at least a ``"text"`` key.  May also
            include ``"provider"``, ``"model"``, ``"tokens"``.
        """
        raise NotImplementedError

    @abstractmethod
    def prepare_context(self, student_id: int) -> Dict[str, Any]:
        """Prepare teacher-specific context for a student.

        Parameters
        ----------
        student_id:
            The ID of the student.

        Returns
        -------
        dict
            Context data for this teacher and student (placeholder).
        """
        raise NotImplementedError

    @abstractmethod
    def available_tools(self) -> List[str]:
        """Return the list of tool names this teacher supports."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def supports_tool(self, tool_name: str) -> bool:
        """Return ``True`` if *tool_name`` is in ``supported_tools``."""
        return tool_name in self.supported_tools

    def supports_topic(self, topic: str) -> bool:
        """Return ``True`` if *topic`` is in ``supported_curriculum``."""
        return topic in self.supported_curriculum

    def to_dict(self) -> Dict[str, Any]:
        """Serialise this teacher's metadata to a plain dict."""
        return {
            "teacher_id": self.teacher_id,
            "subject": self.subject,
            "display_name": self.display_name,
            "description": self.description,
            "supported_curriculum": self.supported_curriculum,
            "supported_tools": self.supported_tools,
            "model_preference": self.model_preference,
            "explanation_style": self.explanation_style,
            "reasoning_style": self.reasoning_style,
            "vocabulary": self.vocabulary,
            "examples": self.examples,
            "preferred_lesson_flow": self.preferred_lesson_flow,
            "correction_style": self.correction_style,
            "teaching_personality": self.teaching_personality,
            "objectives": self.objectives,
            "restrictions": self.restrictions,
            "keywords": self.keywords,
            "difficulty_preference": self.difficulty_preference,
            "curriculum_data": self.curriculum_data,
            "chapters": self.chapters,
            "lessons": self.lessons,
            "competencies": self.competencies,
        }

    def __repr__(self) -> str:
        return f"Teacher(id={self.teacher_id!r}, subject={self.subject!r})"
