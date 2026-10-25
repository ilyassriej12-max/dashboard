"""AI School OS — Phase 4.1 prompt assembly system.

Combines teacher persona, curriculum, student memory, learning style,
mission, conversation history, and system instructions into a single
final prompt string.

No AI call is made here — this module only assembles text.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.memory import Memory
from core.teacher import Teacher


class PromptBuilder:
    """Assembles a complete prompt from discrete context components.

    Each :meth:`build` call produces one final prompt string that a
    provider can consume.  The builder is teacher-agnostic: it accepts
    whatever context the caller supplies and concatenates it in a
    deterministic order.
    """

    # ------------------------------------------------------------------
    # Section templates
    # ------------------------------------------------------------------
    SYSTEM_HEADER = "You are an AI teacher in the AI School OS system.\n"
    PERSONA_TEMPLATE = "\n## Teacher Persona\n{display_name} teaches {subject}.\n{description}\n"
    CURRICULUM_TEMPLATE = "\n## Supported Curriculum\n{curriculum}\n"
    MEMORY_TEMPLATE = "\n## Student Memory\n{memory}\n"
    LEARNING_STYLE_TEMPLATE = "\n## Learning Style\n{learning_style}\n"
    DIFFICULTY_TEMPLATE = "\n## Difficulty Level\n{difficulty}\n"
    MISSION_TEMPLATE = "\n## Current Mission\n{mission}\n"
    HISTORY_TEMPLATE = "\n## Conversation History\n{history}\n"
    INSTRUCTION_TEMPLATE = "\n## System Instructions\n{instructions}\n"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(
        self,
        *,
        teacher: Optional[Teacher] = None,
        persona: Optional[str] = None,
        curriculum: Optional[List[str]] = None,
        memory: Optional[Dict[str, Any]] = None,
        learning_style: Optional[str] = None,
        difficulty: Optional[str] = None,
        mission: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        system_instructions: Optional[str] = None,
        student_id: Optional[int] = None,
        memory_store: Optional[Memory] = None,
    ) -> str:
        """Assemble all supplied context into a single prompt string.

        Parameters are keyword-only.  Any omitted section is simply
        excluded from the final prompt.

        Parameters
        ----------
        teacher:
            Optional :class:`Teacher` instance.  If provided, its
            metadata (name, subject, description, curriculum) is used
            to populate the persona and curriculum sections.
        persona:
            Override for the teacher persona section text.
        curriculum:
            List of curriculum topic strings.
        memory:
            Optional pre-assembled memory dict.  If omitted but
            ``student_id`` and ``memory_store`` are provided, memory
            is loaded from SQLite.
        learning_style:
            Description of the student's learning style.
        mission:
            The student's current learning mission.
        history:
            Optional list of conversation history dicts (each with
            ``role`` and ``message`` keys).
        system_instructions:
            System-level instruction text.
        student_id:
            The student ID, used to load memory from SQLite when
            ``memory`` is not supplied.
        memory_store:
            Optional :class:`Memory` instance.  Required with
            ``student_id`` to auto-load memory.

        Returns
        -------
        str
            The fully assembled prompt string.
        """
        parts: List[str] = [self.SYSTEM_HEADER]

        # --- Teacher persona ---
        if persona is not None:
            parts.append(self.PERSONA_TEMPLATE.format(
                display_name="", subject="", description=persona,
            ))
        elif teacher is not None:
            parts.append(self.PERSONA_TEMPLATE.format(
                display_name=teacher.display_name,
                subject=teacher.subject,
                description=teacher.description,
            ))

        # --- Curriculum ---
        topics = curriculum or (teacher.supported_curriculum if teacher else [])
        if topics:
            curriculum_text = "\n".join(f"- {t}" for t in topics)
            parts.append(self.CURRICULUM_TEMPLATE.format(curriculum=curriculum_text))

        # --- Memory ---
        memory_text = self._format_memory(memory, student_id, memory_store)
        if memory_text:
            parts.append(self.MEMORY_TEMPLATE.format(memory=memory_text))

        # --- Learning style ---
        if learning_style:
            parts.append(self.LEARNING_STYLE_TEMPLATE.format(
                learning_style=learning_style,
            ))

        # --- Difficulty ---
        if difficulty:
            parts.append(self.DIFFICULTY_TEMPLATE.format(difficulty=difficulty))

        # --- Mission ---
        if mission:
            parts.append(self.MISSION_TEMPLATE.format(mission=mission))

        # --- Conversation history ---
        history_text = self._format_history(history)
        if history_text:
            parts.append(self.HISTORY_TEMPLATE.format(history=history_text))

        # --- System instructions ---
        if system_instructions:
            parts.append(self.INSTRUCTION_TEMPLATE.format(
                instructions=system_instructions,
            ))

        return "\n".join(parts).strip() + "\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_memory(
        memory: Optional[Dict[str, Any]],
        student_id: Optional[int],
        memory_store: Optional[Memory],
    ) -> Optional[str]:
        """Format memory into a human-readable block."""
        data: Dict[str, Any] = {}

        if memory:
            data.update(memory)

        if student_id is not None and memory_store is not None:
            state = memory_store.get_state(student_id)
            if state:
                data["current_curriculum"] = state.get("current_curriculum")
                data["current_teacher_id"] = state.get("current_teacher_id")
                data["current_mission"] = state.get("current_mission")
                weak = memory_store.get_weak_topics(student_id)
                if weak:
                    data["weak_topics"] = [w["topic"] for w in weak]
                strong = memory_store.get_strong_topics(student_id)
                if strong:
                    data["strong_topics"] = [s["topic"] for s in strong]

        if not data:
            return None

        lines: List[str] = []
        for key, value in data.items():
            if value is None:
                continue
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                lines.append(f"{label}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{label}: {value}")
        return "\n".join(lines) if lines else None

    @staticmethod
    def _format_history(
        history: Optional[List[Dict[str, Any]]],
    ) -> Optional[str]:
        """Format conversation history into a readable block."""
        if not history:
            return None
        lines: List[str] = []
        for entry in history:
            role = entry.get("role", "unknown")
            message = entry.get("message", "")
            lines.append(f"{role.capitalize()}: {message}")
        return "\n".join(lines)
