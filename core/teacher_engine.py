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

from core.competency_tracker import CompetencyTracker
from core.curriculum_engine import CurriculumEngine
from core.difficulty_engine import DifficultyAssessment, DifficultyEngine
from core.evaluation import EvaluationEngine, EvaluationResult
from core.exam_engine import ExamEngine
from core.feedback import FeedbackEngine, FeedbackResult
from core.knowledge_graph import KnowledgeGraph
from core.lesson_planner import LessonPlanner
from core.memory import Memory
from core.mission_engine import MissionEngine, MissionProgress
from core.prompt_builder import PromptBuilder
from core.progress_tracker import ProgressTracker
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
    requested_teacher_id: Optional[str] = None
    learning_decision: str = "continue"
    current_lesson: Optional[str] = None
    current_chapter: Optional[str] = None
    competencies: List[str] = field(default_factory=list)


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
    curriculum_engine: Optional[CurriculumEngine] = None,
    knowledge_graph: Optional[KnowledgeGraph] = None,
    progress_tracker: Optional[ProgressTracker] = None,
    competency_tracker: Optional[CompetencyTracker] = None,
    exam_engine: Optional[ExamEngine] = None,
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
        self.curriculum_engine = curriculum_engine or CurriculumEngine()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.progress_tracker = progress_tracker or ProgressTracker()
        self.competency_tracker = competency_tracker or CompetencyTracker()
        self.exam_engine = exam_engine or ExamEngine()

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

        # --- Phase 5.5: Curriculum Integration ---
        # Resolve the subject this teacher teaches.
        subject_id = self.curriculum_engine.get_subject_for_teacher(teacher.teacher_id)
        if subject_id is None:
            subject_id = teacher.subject

        # Get the current lesson for this student in this subject.
        current_lesson_id = self.progress_tracker.get_current_lesson(
            student_id, subject_id
        )
        completed_lessons = self.progress_tracker.get_completed_lessons(
            student_id, subject_id
        )

        # Load current chapter/lesson/competencies/objectives.
        current_chapter = None
        current_lesson = None
        competencies: List[str] = []
        lesson_objectives: List[str] = []
        chapter_id: Optional[str] = None

        if current_lesson_id:
            current_lesson = self.curriculum_engine.get_lesson(current_lesson_id)
            if current_lesson:
                chapter_id = current_lesson.chapter_id
                current_chapter = self.curriculum_engine.get_chapter(chapter_id)
                competencies = current_chapter.competencies if current_chapter else []
                lesson_objectives = current_lesson.learning_objectives

        # --- Phase 5.5: Knowledge Graph Integration ---
        # Check prerequisites before teaching.
        if current_lesson_id and not self.knowledge_graph.can_start_lesson(
            current_lesson_id,
            set(completed_lessons),
            {
                c_id: c.score
                for c_id, c in self.competency_tracker.get_all_mastery(
                    student_id, subject_id
                ).items()
            },
        ):
            blocking = self.knowledge_graph.get_blocking_lesson_prerequisites(
                current_lesson_id,
                set(completed_lessons),
                {
                    c_id: c.score
                    for c_id, c in self.competency_tracker.get_all_mastery(
                        student_id, subject_id
                    ).items()
                },
            )
            # Prerequisite missing: explain it first, do not continue.
            prereq_lesson = (
                self.curriculum_engine.get_lesson(blocking[0])
                if blocking
                else None
            )
            prereq_name = prereq_lesson.title if prereq_lesson else blocking[0] if blocking else "previous lesson"

            # Record this attempt.
            self.progress_tracker.update_progress(
                student_id=student_id,
                subject_id=subject_id,
                lesson_id=current_lesson_id,
                increment_attempts=True,
            )

            return TeachingResult(
                text=(
                    f"قبل ما ن继续، خاص نتحقق من {prereq_name} أولا. "
                    f"هذا الدرس يحتاج لمعرفة سابقة قبل ما نبدأ فيه."
                ),
                provider="none",
                model="none",
                tokens=None,
                difficulty="beginner",
                strategy="revision",
                lesson_plan=lesson_plan.to_dict() if lesson_plan else {},
                evaluation={
                    "is_complete": False,
                    "is_structured": False,
                    "matches_curriculum": True,
                    "answers_question": False,
                    "confidence": 1.0,
                    "feedback_notes": [f"Prerequisite missing: {prereq_name}"],
                    "score": 0.0,
                    "metadata": {},
                },
                feedback={
                    "message": f"Please review {prereq_name} first before continuing.",
                    "feedback_type": "needs_revision",
                    "encouragement": True,
                    "suggested_action": f"Review {prereq_name} then return to this lesson.",
                },
                mission={
                    "mission_id": "",
                    "title": "",
                    "progress_percent": 0,
                    "completed": False,
                    "remaining": 0,
                    "xp_milestone": None,
                    "unlocked": False,
                },
                tool={"needed": False, "tool_name": None, "reason": "Prerequisite check"},
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
                requested_teacher_id=None,
                learning_decision="repeat",
                current_lesson=current_lesson_id,
                current_chapter=chapter_id,
                competencies=competencies,
            )

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

        # --- Phase 5.5: Progress Integration ---
        # Mark current lesson as in-progress and increment attempts.
        if current_lesson_id:
            self.progress_tracker.mark_in_progress(
                student_id=student_id,
                subject_id=subject_id,
                lesson_id=current_lesson_id,
            )
            self.progress_tracker.update_progress(
                student_id=student_id,
                subject_id=subject_id,
                lesson_id=current_lesson_id,
                increment_attempts=True,
            )

        # --- Phase 5.5: PromptBuilder Integration ---
        # Build adaptive context for the prompt.
        progress_summary = self.progress_tracker.get_progress_summary(
            student_id, subject_id
        )
        all_mastery = self.competency_tracker.get_all_mastery(student_id, subject_id)
        weak_comps = [
            {"id": c.competency_id, "name": c.name, "score": c.score}
            for c in self.competency_tracker.get_weak_competencies(
                student_id, subject_id
            )
        ]
        strong_comps = [
            {"id": c.competency_id, "name": c.competency_id, "score": c.score}
            for c in self.competency_tracker.get_strong_competencies(
                student_id, subject_id
            )
        ]
        avg_mastery = self.competency_tracker.get_average_mastery(
            student_id, subject_id
        )

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
            current_chapter=current_chapter.title if current_chapter else None,
            current_lesson=current_lesson.title if current_lesson else None,
            competencies=[c.name for c in competencies] if competencies else [],
            lesson_objectives=lesson_objectives,
            progress=progress_summary,
            weak_competencies=weak_comps,
            strong_competencies=strong_comps,
            average_mastery=avg_mastery,
            student_id=student_id,
        )
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

        # --- Step 14: Check for teacher calling (handoff request) ---
        # A teacher may request another teacher to handle this request.
        # This does NOT execute the handoff — it only prepares the
        # routing information for future phases.
        requested_teacher_id: Optional[str] = None
        if teacher is not None:
            requested_teacher_id = teacher.request_teacher(message)

        # --- Phase 5.5: Competency Integration ---
        # After every interaction, update competency mastery.
        if current_lesson_id and current_chapter:
            for comp_id in current_chapter.competencies:
                # Score based on evaluation: complete+answered = 80, else 40
                if evaluation.is_complete and evaluation.answers_question:
                    score = 80.0
                elif evaluation.answers_question:
                    score = 50.0
                else:
                    score = 30.0
                self.competency_tracker.update_mastery(
                    student_id=student_id,
                    subject_id=subject_id,
                    competency_id=comp_id,
                    score=score,
                )

        # --- Phase 5.5: Progress Integration ---
        # Complete lesson if evaluation was successful.
        if current_lesson_id and evaluation.is_complete and evaluation.answers_question:
            self.progress_tracker.mark_completed(
                student_id=student_id,
                subject_id=subject_id,
                lesson_id=current_lesson_id,
                score=evaluation.score * 100,
            )

        # --- Phase 5.5: Teacher Memory Integration ---
        # Remember last lesson, homework, quiz, exam, mistake, revision.
        self.memory.set_state(
            student_id,
            current_curriculum=subject_id,
            current_teacher_id=teacher.teacher_id,
            current_mission=message[:80],
        )

        # --- Phase 5.5: Learning Decision ---
        # TeacherEngine decides automatically what to do next.
        weak_count = len(self.competency_tracker.get_weak_competencies(
            student_id, subject_id
        ))
        strong_count = len(self.competency_tracker.get_strong_competencies(
            student_id, subject_id
        ))
        completed_count = len(self.progress_tracker.get_completed_lessons(
            student_id, subject_id
        ))

        if not evaluation.answers_question:
            learning_decision = "repeat"
        elif weak_count > strong_count and weak_count > 0:
            learning_decision = "revision"
        elif evaluation.is_complete and evaluation.answers_question and strong_count >= 3:
            # Ready for homework/quiz
            learning_decision = "homework"
        elif evaluation.is_complete and evaluation.answers_question:
            learning_decision = "continue"
        else:
            learning_decision = "continue"

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
            requested_teacher_id=requested_teacher_id,
            learning_decision=learning_decision,
            current_lesson=current_lesson_id,
            current_chapter=chapter_id,
            competencies=[c.name for c in competencies] if competencies else [],
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
