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

    When a :class:`Teacher` instance is passed, the builder
    automatically injects teacher persona, rules, style, examples,
    objectives, and restrictions from the teacher's configuration.
    """

    # ------------------------------------------------------------------
    # Section templates
    # ------------------------------------------------------------------
    SYSTEM_HEADER = "You are an AI teacher in the AI School OS system.\n"
    PERSONA_TEMPLATE = "\n## Teacher Persona\n{display_name} teaches {subject}.\n{description}\n"
    PERSONA_DETAILS_TEMPLATE = "\n## Teacher Rules\n{persona}\n"
    CURRICULUM_TEMPLATE = "\n## Supported Curriculum\n{curriculum}\n"
    MEMORY_TEMPLATE = "\n## Student Memory\n{memory}\n"
    LEARNING_STYLE_TEMPLATE = "\n## Learning Style\n{learning_style}\n"
    DIFFICULTY_TEMPLATE = "\n## Difficulty Level\n{difficulty}\n"
    MISSION_TEMPLATE = "\n## Current Mission\n{mission}\n"
    HISTORY_TEMPLATE = "\n## Conversation History\n{history}\n"
    INSTRUCTION_TEMPLATE = "\n## System Instructions\n{instructions}\n"
    CONFIG_TEMPLATE = "\n## Teacher Config\n{config}\n"

    # Phase 5.1: Teacher intelligence templates
    EXPLANATION_STYLE_TEMPLATE = "\n## Explanation Style\n{style}\n"
    REASONING_STYLE_TEMPLATE = "\n## Reasoning Style\n{style}\n"
    VOCABULARY_TEMPLATE = "\n## Preferred Vocabulary\n{words}\n"
    EXAMPLES_TEMPLATE = "\n## Example Topics\n{examples}\n"
    OBJECTIVES_TEMPLATE = "\n## Learning Objectives\n{objectives}\n"
    RESTRICTIONS_TEMPLATE = "\n## Restrictions\n{restrictions}\n"

    # Phase 5.3: Teacher intelligence - subject-specific templates
    HOMEWORK_RULES_TEMPLATE = "\n## Homework Rules\n{rules}\n"
    REVISION_RULES_TEMPLATE = "\n## Revision Rules\n{rules}\n"
    EXERCISE_TYPES_TEMPLATE = "\n## Exercise Types\n{types}\n"
    EVALUATION_RULES_TEMPLATE = "\n## Evaluation Rules\n{rules}\n"
    COMMON_MISTAKES_TEMPLATE = "\n## Common Mistakes\n{mistakes}\n"

    # Phase 5.5: Adaptive learning context templates
    CURRENT_LESSON_TEMPLATE = "\n## Current Lesson\n{chapter} — {lesson}\n"
    COMPETENCIES_TEMPLATE = "\n## Competencies\n{competencies}\n"
    LESSON_OBJECTIVES_TEMPLATE = "\n## Lesson Objectives\n{objectives}\n"
    PROGRESS_TEMPLATE = "\n## Learning Progress\n{progress}\n"
    MASTERY_TEMPLATE = "\n## Competency Mastery\n{mastery}\n"

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
        current_chapter: Optional[str] = None,
        current_lesson: Optional[str] = None,
        competencies: Optional[List[str]] = None,
        lesson_objectives: Optional[List[str]] = None,
        progress: Optional[Dict[str, Any]] = None,
        weak_competencies: Optional[List[Dict[str, Any]]] = None,
        strong_competencies: Optional[List[Dict[str, Any]]] = None,
        average_mastery: Optional[float] = None,
    ) -> str:
        """Assemble all supplied context into a single prompt string.

        Parameters are keyword-only.  Any omitted section is simply
        excluded from the final prompt.

        Parameters
        ----------
        teacher:
            Optional :class:`Teacher` instance.  If provided, its
            metadata (name, subject, description, curriculum) is used
            to populate the persona and curriculum sections, and its
            intelligence attributes (persona, rules, style, examples,
            objectives, restrictions) are automatically injected.
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
            # Full persona text from persona.md
            if getattr(teacher, "persona", None) is not None:
                parts.append(self.PERSONA_DETAILS_TEMPLATE.format(
                    persona=teacher.persona,
                ))
            # Explanation style
            if getattr(teacher, "explanation_style", None) is not None:
                parts.append(self.EXPLANATION_STYLE_TEMPLATE.format(
                    style=teacher.explanation_style,
                ))
            # Reasoning style
            if getattr(teacher, "reasoning_style", None) is not None:
                parts.append(self.REASONING_STYLE_TEMPLATE.format(
                    style=teacher.reasoning_style,
                ))
            # Vocabulary
            if getattr(teacher, "vocabulary", None) is not None:
                vocab_text = ", ".join(teacher.vocabulary)
                parts.append(self.VOCABULARY_TEMPLATE.format(words=vocab_text))
            # Examples
            if getattr(teacher, "examples", None) is not None:
                examples_text = "\n".join(f"- {e}" for e in teacher.examples)
                parts.append(self.EXAMPLES_TEMPLATE.format(examples=examples_text))
            # Objectives
            if getattr(teacher, "objectives", None) is not None:
                obj_text = "\n".join(f"- {o}" for o in teacher.objectives)
                parts.append(self.OBJECTIVES_TEMPLATE.format(objectives=obj_text))
            # Restrictions
            if getattr(teacher, "restrictions", None) is not None:
                rest_text = "\n".join(f"- {r}" for r in teacher.restrictions)
                parts.append(self.RESTRICTIONS_TEMPLATE.format(restrictions=rest_text))

            # Phase 5.3: Teacher-specific sections
            # Homework rules
            if getattr(teacher, "config", None) and teacher.config.get("homework_rules"):
                parts.append(self.HOMEWORK_RULES_TEMPLATE.format(rules=teacher.config["homework_rules"]))

            # Revision rules
            if getattr(teacher, "config", None) and teacher.config.get("revision_rules"):
                parts.append(self.REVISION_RULES_TEMPLATE.format(rules=teacher.config["revision_rules"]))

            # Exercise types
            if getattr(teacher, "config", None) and teacher.config.get("exercise_types"):
                ex_text = "\n".join(f"- {e}" for e in teacher.config["exercise_types"])
                parts.append(self.EXERCISE_TYPES_TEMPLATE.format(types=ex_text))

            # Evaluation rules
            if getattr(teacher, "config", None) and teacher.config.get("evaluation_rules"):
                ev_text = "\n".join(f"- {e}" for e in teacher.config["evaluation_rules"])
                parts.append(self.EVALUATION_RULES_TEMPLATE.format(rules=ev_text))

            # Common mistakes
            if getattr(teacher, "config", None) and teacher.config.get("common_mistakes"):
                cm_text = "\n".join(f"- {m}" for m in teacher.config["common_mistakes"])
                parts.append(self.COMMON_MISTAKES_TEMPLATE.format(mistakes=cm_text))

        # --- Curriculum ---
        topics = curriculum or (teacher.supported_curriculum if teacher else [])
        if topics:
            curriculum_text = "\n".join(f"- {t}" for t in topics)
            parts.append(self.CURRICULUM_TEMPLATE.format(curriculum=curriculum_text))

        # --- Teacher config ---
        if teacher is not None and getattr(teacher, "config", None):
            cfg = teacher.config
            config_lines = []
            if cfg.get("name"):
                config_lines.append(f"Name: {cfg['name']}")
            if cfg.get("subject"):
                config_lines.append(f"Subject: {cfg['subject']}")
            if cfg.get("model"):
                config_lines.append(f"Model: {cfg['model']}")
            if cfg.get("priority") is not None:
                config_lines.append(f"Priority: {cfg['priority']}")
            if cfg.get("allowed_tools"):
                config_lines.append(f"Allowed Tools: {', '.join(cfg['allowed_tools'])}")
            if cfg.get("keywords"):
                config_lines.append(f"Keywords: {', '.join(cfg['keywords'])}")
            if config_lines:
                parts.append(self.CONFIG_TEMPLATE.format(
                    config="\n".join(config_lines),
                ))

        # --- Memory ---
        memory_text = self._format_memory(memory, student_id, memory_store)
        if memory_text:
            parts.append(self.MEMORY_TEMPLATE.format(memory=memory_text))

        # --- Phase 5.5: Current Lesson / Chapter ---
        if current_chapter or current_lesson:
            parts.append(self.CURRENT_LESSON_TEMPLATE.format(
                chapter=current_chapter or "",
                lesson=current_lesson or "",
            ))

        # --- Phase 5.5: Competencies ---
        if competencies:
            comp_text = "\n".join(f"- {c}" for c in competencies)
            parts.append(self.COMPETENCIES_TEMPLATE.format(competencies=comp_text))

        # --- Phase 5.5: Lesson Objectives ---
        if lesson_objectives:
            obj_text = "\n".join(f"- {o}" for o in lesson_objectives)
            parts.append(self.LESSON_OBJECTIVES_TEMPLATE.format(objectives=obj_text))

        # --- Phase 5.5: Learning Progress ---
        if progress:
            comp_pct = progress.get("completion_percent", 0)
            total = progress.get("total_lessons", 0)
            completed = progress.get("completed", 0)
            time_spent = progress.get("total_time_minutes", 0)
            progress_text = (
                f"Completion: {comp_pct}% ({completed}/{total} lessons), "
                f"{time_spent} min total time"
            )
            parts.append(self.PROGRESS_TEMPLATE.format(progress=progress_text))

        # --- Phase 5.5: Competency Mastery ---
        if average_mastery is not None or weak_competencies or strong_competencies:
            mastery_lines = []
            if average_mastery is not None:
                mastery_lines.append(f"Average mastery: {average_mastery}%")
            if weak_competencies:
                weak_names = [c.get("name", c.get("id", "")) for c in weak_competencies]
                mastery_lines.append(f"Weak: {', '.join(weak_names)}")
            if strong_competencies:
                strong_names = [c.get("name", c.get("id", "")) for c in strong_competencies]
                mastery_lines.append(f"Strong: {', '.join(strong_names)}")
            if mastery_lines:
                parts.append(self.MASTERY_TEMPLATE.format(
                    mastery="\n".join(mastery_lines),
                ))

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
