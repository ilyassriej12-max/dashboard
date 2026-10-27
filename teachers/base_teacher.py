"""AI School OS — Phase 4.4 concrete base teacher.

``BaseTeacher`` is a thin coordinator that delegates the full teaching
pipeline to :class:`core.teacher_engine.TeacherEngine`.  Concrete
teachers (e.g. ``MathTeacher``) inherit from this class and contain no
business logic themselves — all teaching intelligence lives in the
Teacher Engine.

Each teacher plugin loads its configuration from ``config.json`` and
its personality from ``persona.md`` automatically via the
:meth:`from_plugin_dir` classmethod.

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
persona:
    Teacher personality text loaded from ``persona.md``.
config:
    Teacher configuration dict loaded from ``config.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
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
        router: Optional[AIRouter] = None,
        memory: Optional[Memory] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        learning_engine: Optional[LearningEngine] = None,
        teacher_engine: Optional[TeacherEngine] = None,
        persona: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        curriculum_engine: Optional[Any] = None,
        knowledge_graph: Optional[Any] = None,
        progress_tracker: Optional[Any] = None,
        competency_tracker: Optional[Any] = None,
        exam_engine: Optional[Any] = None,
    ) -> None:
        super().__init__(
            teacher_id=teacher_id,
            subject=subject,
            display_name=display_name,
            description=description,
            supported_curriculum=supported_curriculum,
            supported_tools=supported_tools,
            model_preference=model_preference,
            explanation_style=explanation_style,
            reasoning_style=reasoning_style,
            vocabulary=vocabulary,
            examples=examples,
            preferred_lesson_flow=preferred_lesson_flow,
            correction_style=correction_style,
            teaching_personality=teaching_personality,
            objectives=objectives,
            restrictions=restrictions,
            keywords=keywords,
            difficulty_preference=difficulty_preference,
        )
        self.router = router
        self.memory = memory
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.learning_engine = learning_engine or LearningEngine()
        self._persona = persona or ""
        self._config = config or {}

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
                lesson_planner=None,
                evaluation_engine=None,
                feedback_engine=None,
                mission_engine=None,
                curriculum_engine=curriculum_engine,
                knowledge_graph=knowledge_graph,
                progress_tracker=progress_tracker,
                competency_tracker=competency_tracker,
                exam_engine=exam_engine,
            )

    # ------------------------------------------------------------------
    # Classmethod factory: load from plugin directory
    # ------------------------------------------------------------------
    @classmethod
    def from_plugin_dir(
        cls,
        plugin_dir: str | Path,
        router: Optional[AIRouter] = None,
        memory: Optional[Memory] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        learning_engine: Optional[LearningEngine] = None,
        teacher_engine: Optional[TeacherEngine] = None,
        persona: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        curriculum_engine: Optional[Any] = None,
        knowledge_graph: Optional[Any] = None,
        progress_tracker: Optional[Any] = None,
        competency_tracker: Optional[Any] = None,
        exam_engine: Optional[Any] = None,
    ) -> "BaseTeacher":
        """Create a teacher instance from a plugin directory.

        The directory must contain ``config.json`` and ``persona.md``.
        The teacher subclass is responsible for knowing its own class;
        this method simply reads the config/persona files and passes
        them to the constructor.

        Parameters
        ----------
        plugin_dir:
            Path to the teacher plugin folder (e.g. ``teachers/math``).
        router, memory, prompt_builder, learning_engine, teacher_engine:
            Optional dependencies passed to the constructor.

        Returns
        -------
        BaseTeacher
            A configured teacher instance.
        """
        plugin_path = Path(plugin_dir).resolve()
        config_path = plugin_path / "config.json"
        persona_path = plugin_path / "persona.md"

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        with open(persona_path, "r", encoding="utf-8") as f:
            persona = f.read()

        return cls(
            teacher_id=config.get("name", plugin_path.name).lower().replace(" ", "_"),
            subject=config.get("subject", plugin_path.name),
            display_name=config.get("name", plugin_path.name),
            description=config.get("description", ""),
            supported_curriculum=config.get("curriculum", []),
            supported_tools=config.get("allowed_tools", []),
            model_preference=config.get("model"),
            router=router,
            memory=memory,
            prompt_builder=prompt_builder,
            learning_engine=learning_engine,
            teacher_engine=teacher_engine,
            persona=persona,
            config=config,
            curriculum_engine=curriculum_engine,
            knowledge_graph=knowledge_graph,
            progress_tracker=progress_tracker,
            competency_tracker=competency_tracker,
            exam_engine=exam_engine,
        )

    # ------------------------------------------------------------------
    # Persona / config accessors
    # ------------------------------------------------------------------
    @property
    def persona(self) -> str:
        """Return the teacher's persona text loaded from ``persona.md``."""
        return self._persona

    @property
    def config(self) -> Dict[str, Any]:
        """Return the teacher's configuration loaded from ``config.json``."""
        return self._config

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
    # Teacher hook methods (Phase 5.3)
    # Subclasses may override these to provide subject-specific behavior.
    # Default implementations delegate to TeacherEngine defaults.
    # ------------------------------------------------------------------

    def prepare_context(self, student_id: int) -> Dict[str, Any]:
        """Prepare teacher-specific context for a student from memory.

        Subclasses may override to add subject-specific context.
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
    # Teacher hook methods (Phase 5.3)
    # Subclasses may override these to provide subject-specific behavior.
    # Default implementations use the teacher's config.json data.
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

    def build_lesson(self, subject: str, difficulty: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Build a lesson plan for the given subject and difficulty.

        Subclasses may override to provide subject-specific lesson plans.
        Uses curriculum data from config.json.
        """
        return {
            "subject": subject,
            "difficulty": difficulty,
            "topic": topic,
            "sections": [],
            "total_duration_minutes": 0,
        }

    def generate_examples(self, topic: str, difficulty: str) -> List[str]:
        """Generate example problems or explanations for a topic.

        Subclasses may override to provide subject-specific examples.
        """
        return []

    def generate_exercises(self, topic: str, difficulty: str) -> List[str]:
        """Generate practice exercises for a topic.

        Subclasses may override to provide subject-specific exercises.
        """
        return []

    def generate_homework(self, student_id: int, difficulty: str) -> Dict[str, Any]:
        """Generate homework assignments for a student.

        Subclasses may override to provide subject-specific homework.
        """
        return {
            "subject": self.subject,
            "difficulty": difficulty,
            "student_id": student_id,
            "assignments": [],
        }

    def generate_revision(self, student_id: int) -> Dict[str, Any]:
        """Generate revision materials for a student.

        Subclasses may override to provide subject-specific revision.
        """
        return {
            "subject": self.subject,
            "student_id": student_id,
            "topics": [],
        }

    def correct_answer(self, answer: str, question: str) -> Dict[str, Any]:
        """Correct a student's answer and provide feedback.

        Subclasses may override to provide subject-specific correction logic.
        """
        return {
            "correct": True,
            "feedback": "Answer recorded.",
            "corrected_answer": answer,
        }

    def evaluate_student(self, answer: str, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate a student's answer.

        Subclasses may override to provide subject-specific evaluation logic.
        """
        return {
            "correct": True,
            "feedback": "Answer received.",
            "score": 1.0,
        }

    def choose_strategy(self, difficulty: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Choose a teaching strategy for the given difficulty and context.

        Subclasses may override to provide subject-specific strategy selection.
        """
        return "explain_first"

    def detect_common_mistakes(self, answer: str, question: str) -> List[str]:
        """Detect common mistakes in a student's answer.

        Subclasses may override to provide subject-specific mistake detection.
        """
        return []

    def recommend_next_step(self, student_id: int, current_topic: str) -> Dict[str, Any]:
        """Recommend the next learning step for a student.

        Subclasses may override to provide subject-specific recommendations.
        """
        return {
            "next_topic": current_topic,
            "reasoning": "Continue with current topic.",
        }

    def summarize_lesson(self, lesson_content: str) -> str:
        """Summarize a lesson for review purposes.

        Subclasses may override to provide subject-specific summarization.
        """
        return lesson_content[:200] + "..." if len(lesson_content) > 200 else lesson_content

    def build_prompt_context(self, student_id: int, message: str) -> Dict[str, Any]:
        """Build prompt context for a student message.

        Subclasses may override to provide subject-specific prompt context.
        """
        return {
            "student_id": student_id,
            "message": message,
            "subject": self.subject,
            "teacher_id": self.teacher_id,
        }

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
