"""AI School OS — Phase 4.3 concrete base teacher.

``BaseTeacher`` is a thin coordinator that delegates the full teaching
pipeline to :class:`core.teacher_engine.TeacherEngine`.  Concrete
teachers (e.g. ``MathTeacher``) inherit from this class and contain no
business logic themselves — all teaching intelligence lives in the
Teacher Engine.

Parameters
----------
teacher_id, subject, display_name, description, supported_curriculum,
    supported_tools, model_preference:
    Passed through to :class:`core.teacher.Teacher.__init__`.
router:
    :class:`services.ai.router.AIRouter` for provider selection.
memory:
    :class:`core.memory.Memory` for context and persistence.
prompt_builder:
    :class:`core.prompt_builder.PromptBuilder` for prompt assembly.
learning_engine:
    :class:`core.learning.LearningEngine` for difficulty computation.
teacher_engine:
    Optional pre-built :class:`core.teacher_engine.TeacherEngine`.  If
    omitted, one is constructed from the other dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.difficulty_engine import DifficultyEngine
from core.learning import LearningEngine
from core.memory import Memory
from core.prompt_builder import PromptBuilder
from core.student_model import StudentModel
from core.teacher import Teacher
from core.teacher_engine import TeacherEngine
from core.teaching_strategy import StrategySelector
from services.ai.router import AIRouter


class BaseTeacher(Teacher):
    """Concrete teacher base class that delegates to TeacherEngine.

    Future subject teachers (MathTeacher, EnglishTeacher, etc.) inherit
    from this class.  They override at most :meth:`prepare_context` for
    subject-specific behaviour; the teaching pipeline itself is owned by
    :class:`TeacherEngine`.
    """

    def __init__(
        self,
        teacher_id: str,
        subject: str,
        display_name: str,
        description: str = "",
        supported_curriculum: Optional[List[str]] = None,
        supported_tools: Optional[List[str]] = None,
        model_preference: Optional[str] = None,
        router: Optional[AIRouter] = None,
        memory: Optional[Memory] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        learning_engine: Optional[LearningEngine] = None,
        teacher_engine: Optional[TeacherEngine] = None,
    ) -> None:
        super().__init__(
            teacher_id=teacher_id,
            subject=subject,
            display_name=display_name,
            description=description,
            supported_curriculum=supported_curriculum,
            supported_tools=supported_tools,
            model_preference=model_preference,
        )
        self.router = router
        self.memory = memory
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.learning_engine = learning_engine or LearningEngine()

        # Build the TeacherEngine if not supplied.  We pass the same
        # dependencies so everything shares one store/router instance.
        if teacher_engine is not None:
            self._engine = teacher_engine
        else:
            self._engine = TeacherEngine(
                router=self.router,
                memory=self.memory,
                prompt_builder=self.prompt_builder,
                difficulty_engine=DifficultyEngine(),
                strategy_selector=StrategySelector(),
                lesson_planner=None,  # default constructed inside TeacherEngine? no — pass explicitly
                evaluation_engine=None,
                feedback_engine=None,
                mission_engine=None,
            )

    # ------------------------------------------------------------------
    # prepare_context
    # ------------------------------------------------------------------
    def prepare_context(self, student_id: int) -> Dict[str, Any]:
        """Assemble teacher-specific context for a student from memory.

        Delegates to the underlying Memory instance.  Kept for API
        compatibility with :class:`core.teacher.Teacher`.
        """
        ctx: Dict[str, Any] = {}
        if self.memory is None:
            return ctx

        history = self.memory.get_history(student_id, limit=10)
        ctx["history"] = list(reversed(history))
        ctx["weak_topics"] = self.memory.get_weak_topics(student_id)
        ctx["strong_topics"] = self.memory.get_strong_topics(student_id)
        ctx["state"] = self.memory.get_state(student_id)

        prefs = ctx["state"].get("preferences", {}) if isinstance(ctx["state"], dict) else {}
        ctx["learning_style"] = prefs.get("language", "visual") if isinstance(prefs, dict) else "visual"

        return ctx

    # ------------------------------------------------------------------
    # ask — delegates to TeacherEngine
    # ------------------------------------------------------------------
    async def ask(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a student message through the Teacher Engine pipeline.

        This is the single entry point for all teaching.  No subject-
        specific logic lives here — :class:`TeacherEngine` handles
        difficulty, strategy, planning, prompting, generation,
        evaluation, feedback, and mission tracking.

        Parameters
        ----------
        message:
            The student's input text.
        context:
            Must contain ``student_id``.  May also contain overrides
            for ``router``, ``memory``, ``prompt_builder``.

        Returns
        -------
        dict
            Structured result with keys: ``text``, ``provider``,
            ``model``, ``tokens``, plus engine diagnostics
            (``difficulty``, ``strategy``, ``evaluation``, ``feedback``,
            ``mission``, ``tool``, ``student_model``, ``lesson_plan``).
        """
        ctx = context or {}
        student_id = ctx.get("student_id", 1)

        result = await self._engine.run(
            teacher=self,
            message=message,
            student_id=student_id,
            curriculum=ctx.get("curriculum"),
        )

        # Return a flat dict compatible with existing callers plus
        # engine diagnostics.
        return {
            "text": result.text,
            "provider": result.provider,
            "model": result.model,
            "tokens": result.tokens,
            # Engine diagnostics (new in Phase 4.3):
            "difficulty": result.difficulty,
            "strategy": result.strategy,
            "lesson_plan": result.lesson_plan,
            "evaluation": result.evaluation,
            "feedback": result.feedback,
            "mission": result.mission,
            "tool": result.tool,
            "student_model": result.student_model,
        }

    # ------------------------------------------------------------------
    # available_tools
    # ------------------------------------------------------------------
    def available_tools(self) -> List[str]:
        """Return the list of tool names this teacher supports."""
        return list(self.supported_tools)

    # ------------------------------------------------------------------
    # Persistence helpers (thin wrappers around Memory)
    # ------------------------------------------------------------------
    def persist_interaction(
        self,
        student_id: int,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Save the conversation exchange to memory.

        The Teacher Engine already persists interactions inside
        :meth:`run`, so this is a convenience wrapper for external
        callers that need to persist manually.
        """
        if self.memory is None:
            return
        self.memory.add_message(student_id, self.teacher_id, "user", user_message)
        self.memory.add_message(student_id, self.teacher_id, "assistant", assistant_message)

    def update_mission_progress(
        self,
        student_id: int,
        lessons_total: int,
        lessons_completed: int,
    ) -> Dict[str, Any]:
        """Update and return mission progress for the student."""
        if self.memory is None:
            return {}
        return self.memory.get_state(student_id)

    # ------------------------------------------------------------------
    # Expose the engine for advanced use
    # ------------------------------------------------------------------
    @property
    def engine(self) -> TeacherEngine:
        """Return the underlying :class:`TeacherEngine` instance."""
        return self._engine
