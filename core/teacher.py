"""AI School OS — Phase 4.1 abstract Teacher class.

Every teacher in future phases must inherit from :class:`Teacher`.
This class defines the *shape* of a teacher — identity, capabilities,
and behaviour contracts — without implementing any AI generation.

Responsibilities:

* teacher id, subject, display name, description
* supported curriculum and tools
* model preference
* :meth:`ask` — process a student message (placeholder)
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
    ) -> None:
        self.teacher_id = teacher_id
        self.subject = subject
        self.display_name = display_name
        self.description = description
        self.supported_curriculum = supported_curriculum or []
        self.supported_tools = supported_tools or []
        self.model_preference = model_preference

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
        }

    def __repr__(self) -> str:
        return f"Teacher(id={self.teacher_id!r}, subject={self.subject!r})"
