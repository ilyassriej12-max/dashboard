"""AI School OS — Phase 4.3 Student Model.

Represents the current learner state.  Pure logic — no AI calls, no
database writes.  All fields are derived from the existing
:class:`core.memory.Memory` layer and in-memory computation.

The :class:`StudentModel` is a read-only snapshot that the Teacher
Engine consumes when deciding how to teach a student.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StudentModel:
    """Snapshot of a learner's current state.

    Attributes
    ----------
    student_id:
        Unique identifier for the student.
    knowledge_level:
        Assessed overall knowledge level (``"beginner"``, ``"easy"``,
        ``"medium"``, ``"advanced"``, ``"expert"``).
    learning_style:
        Preferred learning style string (e.g. ``"visual"``,
        ``"auditory"``, ``"reading/writing"``, ``"kinesthetic"``).
    recent_mistakes:
        List of recent mistake topic strings.
    strong_topics:
        List of topics the student has demonstrated strength in.
    weak_topics:
        List of topics the student struggles with.
    attention:
        Estimated attention/focus level (0.0 to 1.0).
    mission_progress:
        Progress percentage toward the current mission (0 to 100).
    current_curriculum:
        The curriculum/subject currently being studied.
    raw_state:
        The raw memory-state dict for reference.
    """

    student_id: int
    knowledge_level: str = "beginner"
    learning_style: str = "visual"
    recent_mistakes: List[str] = field(default_factory=list)
    strong_topics: List[str] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    attention: float = 0.5
    mission_progress: float = 0.0
    current_curriculum: Optional[str] = None
    raw_state: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_memory(
        cls,
        student_id: int,
        memory: Any,
        knowledge_level: str = "beginner",
    ) -> "StudentModel":
        """Build a :class:`StudentModel` from a :class:`Memory` instance.

        Parameters
        ----------
        student_id:
            The student to model.
        memory:
            A :class:`Memory` instance (or any object with the same
            methods: ``get_state``, ``get_weak_topics``,
            ``get_strong_topics``, ``get_mistakes``).
        knowledge_level:
            Pre-computed knowledge level from the difficulty engine.
        """
        state = memory.get_state(student_id) if memory else {}
        weak = memory.get_weak_topics(student_id) if memory else []
        strong = memory.get_strong_topics(student_id) if memory else []
        mistakes = memory.get_mistakes(student_id) if memory else []

        return cls(
            student_id=student_id,
            knowledge_level=knowledge_level,
            learning_style=(state.get("preferences", {}).get("language", "visual")
                            if isinstance(state.get("preferences"), dict)
                            else "visual"),
            recent_mistakes=[m.get("topic", "") for m in mistakes][:5],
            strong_topics=[t.get("topic", "") for t in strong],
            weak_topics=[t.get("topic", "") for t in weak],
            attention=0.5,
            mission_progress=float(state.get("mission_progress", 0)
                                   if isinstance(state.get("mission_progress"), (int, float))
                                   else 0.0),
            current_curriculum=state.get("current_curriculum"),
            raw_state=state,
        )
