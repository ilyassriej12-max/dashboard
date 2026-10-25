"""AI School OS — Phase 4.3 Teacher Engine.

The Teacher Engine is the internal intelligence layer that every future
teacher plugin uses.  It orchestrates the full teaching pipeline:

1. Receive request
2. Analyze student (StudentModel)
3. Read memory
4. Analyze curriculum
5. Determine difficulty (DifficultyEngine)
6. Choose teaching strategy (TeachingStrategy)
7. Build lesson (LessonPlanner)
8. Determine tool need
9. Generate prompt (PromptBuilder)
10. Call AI (via router/provider)
11. Evaluate answer (EvaluationEngine)
12. Update learning state (Memory)
13. Return structured result

Future teachers (MathTeacher, EnglishTeacher, etc.) inherit from
:class:`BaseTeacher` and delegate :meth:`Teacher.ask` to
:meth:`TeacherEngine.run`.  They contain no business logic themselves.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.difficulty_engine import DifficultyAssessment, DifficultyEngine
from core.evaluation import EvaluationEngine, EvaluationResult
from core.feedback import FeedbackEngine, FeedbackResult
from core.lesson_planner import LessonPlanner
from core.memory import Memory
from core.mission_engine import MissionEngine, MissionProgress
from core.prompt_builder import PromptBuilder
from core.student_model import StudentModel
from core.teaching_strategy import StrategySelector, TeachingStrategy
from core.teacher import Teacher
from services.ai.router import AIRouter


@dataclass
class ToolDecision:
    """Whether a tool is needed and which one.

    Attributes
    ----------
    needed:
        Whether a tool should be used.
    tool_name:
        The tool name, or ``None``.
    reason:
        Explanation for the decision.
    """

    needed: bool = False
    tool_name: Optional[str] = None
    reason: str = ""


@dataclass
class TeachingResult:
    """The complete result of a teaching session.

    Attributes
    ----------
    text:
        The AI-generated answer text.
    provider:
        The provider ID used (e.g. ``"ollama"``, ``"gemini"``).
    model:
        The model identifier.
    tokens:
        Token count from the provider, if available.
    difficulty:
        The assessed difficulty level.
    strategy:
        The selected teaching strategy name.
    lesson_plan:
        Serialised lesson plan dict.
    evaluation:
        Serialised evaluation result dict.
    feedback:
        Serialised feedback result dict.
    mission:
        Serialised mission progress dict.
    tool:
        Serialised tool decision dict.
    student_model:
        Serialised student model dict.
    """

    text: str
    provider: str
    model: str
    tokens: Optional[int]
    difficulty: str
    strategy: str
    lesson_plan: Dict[str, Any]
    evaluation: Dict[str, Any]
    feedback: Dict[str, Any]
    mission: Dict[str, Any]
    tool: Dict[str, Any]
    student_model: Dict[str, Any]


class TeacherEngine:
    """The central teaching pipeline.

    Orchestrates all Phase 4.3 sub-engines to produce a complete
    teaching response.  Dependencies are injected so the engine is
    easy to test and extend.

    Parameters
    ----------
    router:
        :class:`AIRouter` for provider selection.
    memory:
        :class:`Memory` for reading/writing student state.
    prompt_builder:
        :class:`PromptBuilder` for assembling prompts.
    difficulty_engine:
        :class:`DifficultyEngine` for assessing difficulty.
    strategy_selector:
        :class:`StrategySelector` for choosing teaching strategies.
    lesson_planner:
        :class:`LessonPlanner` for building lesson plans.
    evaluation_engine:
        :class:`EvaluationEngine` for evaluating responses.
    feedback_engine:
        :class:`FeedbackEngine` for generating feedback.
    mission_engine:
        :class:`MissionEngine` for mission tracking.
    """

    def __init__(
        self,
        router: AIRouter,
        memory: Memory,
        prompt_builder: PromptBuilder,
        difficulty_engine: Optional[DifficultyEngine] = None,
        strategy_selector: Optional[StrategySelector] = None,
        lesson_planner: Optional[LessonPlanner] = None,
        evaluation_engine: Optional[EvaluationEngine] = None,
        feedback_engine: Optional[FeedbackEngine] = None,
        mission_engine: Optional[MissionEngine] = None,
    ) -> None:
        self.router = router
        self.memory = memory
        self.prompt_builder = prompt_builder
        self.difficulty_engine = difficulty_engine or DifficultyEngine()
        self.strategy_selector = strategy_selector or StrategySelector()
        self.lesson_planner = lesson_planner or LessonPlanner()
        self.evaluation_engine = evaluation_engine or EvaluationEngine()
        self.feedback_engine = feedback_engine or FeedbackEngine()
        self.mission_engine = mission_engine or MissionEngine()

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------
    async def run(
        self,
        teacher: Teacher,
        message: str,
        student_id: int,
        curriculum: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeachingResult:
        """Execute the full teaching pipeline.

        Parameters
        ----------
        teacher:
            The :class:`Teacher` instance handling the request.
        message:
            The student's input text.
        student_id:
            The ID of the student.
        curriculum:
            Optional subject/curriculum hint.
        context:
            Additional context (unused here, reserved for extensions).

        Returns
        -------
        TeachingResult
            A fully populated result with answer, provider info,
            evaluation, feedback, mission progress, and more.
        """
        ctx = context or {}

        # --- Step 1-3: Analyze student + read memory ---
        # Determine difficulty first (needs memory for weak/strong topics).
        difficulty_assessment: DifficultyAssessment = (
            self.difficulty_engine.assess(student_id, teacher.subject, self.memory)
        )
        difficulty = difficulty_assessment.level

        # Build the student model.
        model = StudentModel.from_memory(
            student_id=student_id,
            memory=self.memory,
            knowledge_level=difficulty,
        )

        # --- Step 4: Choose teaching strategy ---
        strategy: TeachingStrategy = self.strategy_selector.select(
            difficulty=difficulty,
            weak_topics=model.weak_topics,
            strong_topics=model.strong_topics,
            mission_progress=model.mission_progress,
        )

        # --- Step 5: Build lesson plan ---
        lesson_plan = self.lesson_planner.plan(
            student_id=student_id,
            subject=teacher.subject,
            difficulty=difficulty,
            strategy_name=strategy.name,
            topic=curriculum,
        )

        # --- Step 6: Determine tool need ---
        tool_decision = self._decide_tool(message, strategy, difficulty)

        # --- Step 7: Generate prompt ---
        history = self.memory.get_history(student_id, limit=10)
        history_chronological = list(reversed(history))
        prompt = self.prompt_builder.build(
            teacher=teacher,
            curriculum=teacher.supported_curriculum,
            memory={
                "Weak Topics": ", ".join(model.weak_topics) or "None recorded",
                "Strong Topics": ", ".join(model.strong_topics) or "None recorded",
            },
            learning_style=model.learning_style,
            difficulty=difficulty,
            mission=model.raw_state.get("current_mission"),
            history=history_chronological,
            system_instructions=(
                "You are a helpful, encouraging AI teacher. "
                "Answer the student's question clearly and accurately. "
                "Adapt your explanation to the student's difficulty level "
                "and learning style. Follow the selected teaching strategy."
            ),
        )

        # --- Step 8-10: Call AI (with fallback) ---
        generation_result = await self._generate_with_fallback(
            router=self.router,
            preferred_model=teacher.model_preference,
            prompt=prompt,
        )
        provider = generation_result["provider"]
        model_name = generation_result["model"]
        answer_text = generation_result["text"]
        tokens = generation_result.get("tokens")

        # --- Step 11: Evaluate answer ---
        evaluation: EvaluationResult = self.evaluation_engine.evaluate(
            question=message,
            answer=answer_text,
            curriculum=teacher.supported_curriculum,
        )

        # --- Step 12: Update learning state ---
        self._update_learning_state(
            student_id=student_id,
            teacher=teacher,
            message=message,
            answer=answer_text,
            evaluation=evaluation,
            model=model,
            difficulty=difficulty,
        )

        # Mission progress update.
        mission: MissionProgress = self.mission_engine.daily_mission(
            student_id=student_id,
            subject=teacher.subject,
        )

        # --- Step 13: Generate feedback ---
        feedback: FeedbackResult = self.feedback_engine.generate(
            evaluation=evaluation,
            model=model,
            difficulty=difficulty,
        )

        # --- Return structured result ---
        return TeachingResult(
            text=answer_text,
            provider=provider,
            model=model_name,
            tokens=tokens,
            difficulty=difficulty,
            strategy=strategy.name,
            lesson_plan=lesson_plan.to_dict(),
            evaluation={
                "is_complete": evaluation.is_complete,
                "is_structured": evaluation.is_structured,
                "matches_curriculum": evaluation.matches_curriculum,
                "answers_question": evaluation.answers_question,
                "confidence": evaluation.confidence,
                "feedback_notes": evaluation.feedback_notes,
                "score": evaluation.score,
                "metadata": evaluation.metadata,
            },
            feedback={
                "message": feedback.message,
                "feedback_type": feedback.feedback_type,
                "encouragement": feedback.encouragement,
                "suggested_action": feedback.suggested_action,
            },
            mission={
                "mission_id": mission.mission_id,
                "title": mission.title,
                "progress_percent": mission.progress_percent,
                "completed": mission.completed,
                "remaining": mission.remaining,
                "xp_milestone": mission.xp_milestone,
                "unlocked": mission.unlocked,
            },
            tool={
                "needed": tool_decision.needed,
                "tool_name": tool_decision.tool_name,
                "reason": tool_decision.reason,
            },
            student_model={
                "student_id": model.student_id,
                "knowledge_level": model.knowledge_level,
                "learning_style": model.learning_style,
                "recent_mistakes": model.recent_mistakes,
                "strong_topics": model.strong_topics,
                "weak_topics": model.weak_topics,
                "attention": model.attention,
                "mission_progress": model.mission_progress,
                "current_curriculum": model.current_curriculum,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _generate_with_fallback(
        self,
        router: AIRouter,
        preferred_model: Optional[str],
        prompt: str,
    ) -> Dict[str, Any]:
        """Generate a response using the selected provider, with fallback.

        Parameters
        ----------
        router:
            The :class:`AIRouter` instance.
        preferred_model:
            The teacher's preferred model, if any.
        prompt:
            The assembled prompt text.

        Returns
        -------
        dict
            Provider result with ``text``, ``provider``, ``model``,
            ``tokens``.
        """
        selection = router.select_provider(
            request_type="chat",
            preferred_model=preferred_model,
        )
        provider = router.get_provider(selection.provider_id)
        if provider is None:
            return {
                "text": "Error: no AI provider available.",
                "provider": "none",
                "model": "none",
                "tokens": None,
            }

        try:
            result = await provider.generate(prompt)
        except Exception:
            # Primary failed — try fallback.
            fb_selection = router.fallback(selection.provider_id)
            fb_provider = router.get_provider(fb_selection.provider_id)
            if fb_provider is None:
                return {
                    "text": "Error: primary provider failed and no fallback available.",
                    "provider": selection.provider_id,
                    "model": provider.model,
                    "tokens": None,
                }
            try:
                result = await fb_provider.generate(prompt)
                provider = fb_provider
                selection = fb_selection
            except Exception as exc:
                return {
                    "text": f"Error: all providers failed. Last error: {exc}",
                    "provider": "none",
                    "model": "none",
                    "tokens": None,
                }

        return {
            "text": result.get("text", ""),
            "provider": provider.provider_id,
            "model": provider.model,
            "tokens": result.get("tokens"),
        }

    @staticmethod
    def _decide_tool(
        message: str,
        strategy: TeachingStrategy,
        difficulty: str,
    ) -> ToolDecision:
        """Decide whether a tool is needed for this request.

        Parameters
        ----------
        message:
            The student's input text.
        strategy:
            The selected teaching strategy.
        difficulty:
            The assessed difficulty level.

        Returns
        -------
        ToolDecision
        """
        tool_keywords = (
            "draw", "diagram", "graph", "plot", "whiteboard",
            "sketch", "visualize", "chart",
        )
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in tool_keywords):
            return ToolDecision(
                needed=True,
                tool_name="whiteboard",
                reason="Student requested a drawing or diagram.",
            )
        if difficulty in ("advanced", "expert") and strategy.name == "challenge":
            return ToolDecision(
                needed=False,
                tool_name=None,
                reason="Advanced challenge — no tool required.",
            )
        return ToolDecision(
            needed=False,
            tool_name=None,
            reason="No tool indicated by the request.",
        )

    def _update_learning_state(
        self,
        student_id: int,
        teacher: Teacher,
        message: str,
        answer: str,
        evaluation: EvaluationResult,
        model: StudentModel,
        difficulty: str,
    ) -> None:
        """Persist the interaction and update weak/strong topics.

        Parameters
        ----------
        student_id:
            The student.
        teacher:
            The teacher handling the request.
        message:
            The student's message.
        answer:
            The AI's answer.
        evaluation:
            The evaluation result.
        model:
            The student model.
        difficulty:
            The assessed difficulty level.
        """
        if self.memory is None:
            return

        # Persist conversation exchange.
        self.memory.add_message(student_id, teacher.teacher_id, "user", message)
        self.memory.add_message(student_id, teacher.teacher_id, "assistant", answer)

        # Heuristic: track mistakes on weak-topic keywords in the question.
        lower = message.lower()
        for topic in model.weak_topics:
            if topic.lower() in lower:
                self.memory.record_mistake(student_id, topic, teacher.subject)
                break

        # If the answer was complete and structured, mark strong topics.
        if evaluation.is_complete and evaluation.is_structured:
            for topic in model.strong_topics:
                self.memory.set_strong_topic(
                    student_id, topic, teacher.subject, score=0.7
                )
