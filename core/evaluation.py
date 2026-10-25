"""AI School OS — Phase 4.3 Evaluation Engine.

Evaluates AI-generated responses for quality, completeness, and
curriculum alignment.  Pure logic — no AI calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvaluationResult:
    """Result of evaluating an AI response.

    Attributes
    ----------
    is_complete:
        Whether the answer fully addresses the student's question.
    is_structured:
        Whether the explanation has clear structure (headings, steps,
        etc.).
    matches_curriculum:
        Whether the content stays within the expected curriculum.
    answers_question:
        Whether the response directly answers what was asked.
    confidence:
        Overall confidence in the evaluation (0.0 to 1.0).
    feedback_notes:
        List of specific observations about the response.
    metadata:
        Additional evaluation metadata (word count, etc.).
    """

    is_complete: bool = False
    is_structured: bool = False
    matches_curriculum: bool = True
    answers_question: bool = False
    confidence: float = 0.5
    feedback_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """Overall evaluation score (0.0 to 1.0)."""
        factors = [
            (self.is_complete, 0.30),
            (self.answers_question, 0.30),
            (self.is_structured, 0.20),
            (self.matches_curriculum, 0.20),
        ]
        return sum(weight for flag, weight in factors if flag)


class EvaluationEngine:
    """Evaluates AI-generated responses against quality criteria.

    Uses deterministic heuristics (no AI).  The engine inspects the
    response text for structural signals, length, keyword overlap with
    the question, and curriculum markers.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate(
        self,
        question: str,
        answer: str,
        curriculum: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate an AI response.

        Parameters
        ----------
        question:
            The student's original question.
        answer:
            The AI-generated response text.
        curriculum:
            Optional list of curriculum topic strings.
        context:
            Additional context (unused here, reserved for extensions).

        Returns
        -------
        EvaluationResult
        """
        ctx = context or {}

        words = answer.split()
        word_count = len(words)

        # Completeness: answer has substantial length and ends with a
        # period or clear closing.
        is_complete = word_count >= 15 and answer.strip().endswith((".", "!", "?", "”"))

        # Structured: contains line breaks, bullets, or numbered steps.
        is_structured = (
            "\n" in answer
            or any(line.strip().startswith(("-", "*", "1.", "2.", "3.")) for line in answer.splitlines())
        )

        # Answers question: shares at least one content word with the
        # question (excluding stop words).
        answers_question = self._shares_content_words(question, answer)

        # Matches curriculum: no obvious out-of-scope technical terms
        # when curriculum is provided.
        matches_curriculum = True
        if curriculum:
            curriculum_lc = [c.lower() for c in curriculum]
            # Simple check: if answer mentions "quantum physics" but
            # curriculum is "basic arithmetic", flag it.
            # (This is a heuristic placeholder; future phases can refine.)
            matches_curriculum = True

        # Confidence based on signal strength.
        confidence = min(0.9, 0.4 + 0.1 * min(word_count, 50) / 50)

        notes: List[str] = []
        if not is_complete:
            notes.append("Answer may be too brief or abruptly ended.")
        if not is_structured:
            notes.append("Consider adding structure (steps, bullets).")
        if not answers_question:
            notes.append("Response may not directly address the question.")
        if not matches_curriculum:
            notes.append("Content may extend beyond the current curriculum.")

        metadata: Dict[str, Any] = {
            "word_count": word_count,
            "char_count": len(answer),
            "question_word_count": len(question.split()),
        }

        return EvaluationResult(
            is_complete=is_complete,
            is_structured=is_structured,
            matches_curriculum=matches_curriculum,
            answers_question=answers_question,
            confidence=confidence,
            feedback_notes=notes,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _shares_content_words(question: str, answer: str) -> bool:
        """Return True if question and answer share non-stop words."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "to",
            "of", "in", "for", "on", "with", "at", "by", "from", "as",
            "i", "you", "he", "she", "it", "we", "they", "what", "who",
            "where", "when", "why", "how", "?", ".", ",", "!",
        }
        q_words = {w.lower().strip(".,!?") for w in question.split() if w.lower() not in stop_words}
        a_words = {w.lower().strip(".,!?") for w in answer.split() if w.lower() not in stop_words}
        return len(q_words & a_words) > 0
