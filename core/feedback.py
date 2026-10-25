"""AI School OS — Phase 4.3 Feedback Engine.

Generates structured feedback for the student based on evaluation
results and learning state.  Pure logic — no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.evaluation import EvaluationResult
from core.student_model import StudentModel


@dataclass
class FeedbackResult:
    """Structured feedback for a student.

    Attributes
    ----------
    message:
        Human-readable feedback message.
    feedback_type:
        One of ``"great_progress"``, ``"needs_revision"``,
        ``"recommend_quiz"``, ``"suggest_another_explanation"``,
        ``"recommend_discussion"``, ``"recommend_another_teacher"``.
    encouragement:
        Whether the message is encouraging (vs corrective).
    suggested_action:
        Optional next action for the student or system.
    """

    message: str
    feedback_type: str
    encouragement: bool = True
    suggested_action: Optional[str] = None


class FeedbackEngine:
    """Generates feedback based on evaluation results and student state.

    Uses deterministic rules — no AI calls.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        evaluation: EvaluationResult,
        model: StudentModel,
        difficulty: str = "medium",
    ) -> FeedbackResult:
        """Generate feedback for a student based on evaluation results.

        Parameters
        ----------
        evaluation:
            The result of evaluating the AI's response.
        model:
            The student's current model.
        difficulty:
            The difficulty level of the current lesson.

        Returns
        -------
        FeedbackResult
        """
        # High-quality response + strong student -> great progress.
        if evaluation.score >= 0.8 and len(model.strong_topics) > len(model.weak_topics):
            return FeedbackResult(
                message="Great progress! You're mastering this material well.",
                feedback_type="great_progress",
                encouragement=True,
                suggested_action="Continue to the next topic or attempt a practice quiz.",
            )

        # Complete but unstructured -> suggest another explanation.
        if evaluation.is_complete and not evaluation.is_structured:
            return FeedbackResult(
                message="The answer was correct but could be clearer. Let me try explaining it differently.",
                feedback_type="suggest_another_explanation",
                encouragement=True,
                suggested_action="Request a simplified explanation.",
            )

        # Didn't answer the question -> recommend discussion.
        if not evaluation.answers_question:
            return FeedbackResult(
                message="I may not have fully addressed your question. Could you rephrase it?",
                feedback_type="recommend_discussion",
                encouragement=True,
                suggested_action="Rephrase your question with more detail.",
            )

        # Many weak topics -> needs revision.
        if len(model.weak_topics) >= 3:
            return FeedbackResult(
                message="It looks like you could benefit from reviewing some foundational topics first.",
                feedback_type="needs_revision",
                encouragement=True,
                suggested_action="Review previous lessons on your weak topics.",
            )

        # Low difficulty but struggling -> recommend quiz to confirm.
        if difficulty in ("beginner", "easy") and evaluation.score < 0.6:
            return FeedbackResult(
                message="Let's check your understanding with a quick quiz before moving on.",
                feedback_type="recommend_quiz",
                encouragement=True,
                suggested_action="Take a short quiz on this topic.",
            )

        # Default fallback.
        return FeedbackResult(
            message="Keep practicing — you're making progress step by step.",
            feedback_type="great_progress",
            encouragement=True,
            suggested_action="Continue with the next exercise.",
        )

    def list_feedback_types(self) -> List[str]:
        """Return all available feedback type identifiers."""
        return [
            "great_progress",
            "needs_revision",
            "recommend_quiz",
            "suggest_another_explanation",
            "recommend_discussion",
            "recommend_another_teacher",
        ]
