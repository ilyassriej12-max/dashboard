"""AI School OS — Phase 4.1 central decision engine (orchestrator).

The orchestrator receives a student request and returns routing
information — which teacher should answer, whether multiple teachers
are required, and whether a tool will be needed later.

No LLM calls are made here.  No answers are generated.  This is
architecture only: the decision rules that Phase 4.2+ will refine.

Phase 5.1 improvements:
- Keyword-based teacher routing (math -> MathTeacher, coding ->
  ProgrammingTeacher, grammar -> EnglishTeacher, etc.)
- Multi-teacher request detection for mixed queries
- Teacher calling preparation (teachers may request another teacher)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.loader import get_teacher, list_teachers
from core.memory import Memory
from core.prompt_builder import PromptBuilder
from core.teacher import Teacher
from core.teacher_engine import TeacherEngine
from core.learning import LearningEngine
from services.ai.router import AIRouter


@dataclass
class RoutingDecision:
    """Result of an orchestrator routing decision.

    Attributes
    ----------
    teacher_id:
        ID of the primary teacher selected to handle the request.
    requires_multiple_teachers:
        Whether the request should be split across multiple teachers.
    requires_tool:
        Whether a tool (e.g. whiteboard, calculator) is anticipated.
    reasoning:
        Human-readable explanation of the routing decision.
    candidate_teachers:
        IDs of all teachers considered, in priority order.
    requested_teacher_id:
        ID of a teacher that the requesting teacher wants to hand off
        to (Phase 5.1 preparation — not executed yet).
    """

    teacher_id: Optional[str]
    requires_multiple_teachers: bool = False
    requires_tool: bool = False
    reasoning: str = ""
    candidate_teachers: List[str] = field(default_factory=list)
    requested_teacher_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teacher_id": self.teacher_id,
            "requires_multiple_teachers": self.requires_multiple_teachers,
            "requires_tool": self.requires_tool,
            "reasoning": self.reasoning,
            "candidate_teachers": self.candidate_teachers,
            "requested_teacher_id": self.requested_teacher_id,
        }


class Orchestrator:
    """Central decision engine for request routing.

    Responsibilities:

    * Receive a student request.
    * Determine which teacher should answer.
    * Determine whether multiple teachers are required.
    * Determine whether a tool will be required later.

    Returns routing information only.  The caller is responsible for
    instantiating the selected teacher and calling :meth:`Teacher.ask`.
    """

    # ------------------------------------------------------------------
    # Keyword -> teacher_id mapping for keyword-based routing
    # ------------------------------------------------------------------
    SUBJECT_KEYWORDS: Dict[str, List[str]] = {
        "mathematics": [
            "math", "mathematics", "algebra", "calculus", "equation",
            "solve", "derivative", "integral", "geometry", "triangle",
            "circle", "matrix", "vector", "statistic", "probability",
            "arithmetic", "polynomial", "trigonometry",
        ],
        "english": [
            "grammar", "spelling", "vocabulary", "english", "literature",
            "writing", "essay", "poem", "poetry", "reading", "novel",
            "author", "syntax", "punctuation", "sentence",
        ],
        "physics": [
            "physics", "mechanics", "waves", "energy", "force", "motion",
            "quantum", "relativity", "electricity", "magnetism",
            "thermodynamics", "particle", "atom", "photon",
        ],
        "chemistry": [
            "chemistry", "chemical", "molecule", "reaction", "element",
            "compound", "acid", "base", "organic", "inorganic",
            "periodic", "atom", "bond", "oxidation", "reduction",
        ],
        "svt": [
            "svt", "biology", "life science", "cell", "dna", "gene",
            "ecosystem", "photosynthesis", "evolution", "anatomy",
            "physiology", "organism", "plant", "animal",
        ],
        "philosophy": [
            "philosophy", "philosophical", "ethics", "logic",
            "argument", "reasoning", "metaphysics", "epistemology",
            "existentialism", "stoicism", "morality", "truth",
            "knowledge", "reality", "consciousness",
        ],
        "german": [
            "german", "deutsch", "grammar", "vocabulary", "sentence",
            "verb", "noun", "article", "case", "conjugation",
            "translation", "pronunciation", "umlaut",
        ],
    }

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._teachers_loaded: bool = False

    def ensure_teachers_loaded(
        self,
        router: Optional[AIRouter] = None,
        memory: Optional[Memory] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        learning_engine: Optional[LearningEngine] = None,
        teacher_engine: Optional[TeacherEngine] = None,
    ) -> None:
        """Trigger plugin discovery if not yet done.

        Dependencies are passed through to each teacher plugin via
        :func:`core.loader.load_teachers`.
        """
        if not self._teachers_loaded:
            # Import here to avoid circular imports at module load time.
            from core.loader import load_teachers

            load_teachers(
                router=router,
                memory=memory,
                prompt_builder=prompt_builder,
                learning_engine=learning_engine,
                teacher_engine=teacher_engine,
            )
            self._teachers_loaded = True

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def route(
        self,
        student_request: str,
        student_id: int,
        subject: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Route a student request to the appropriate teacher.

        Parameters
        ----------
        student_request:
            The student's input text.
        student_id:
            The ID of the student making the request.
        subject:
            Optional subject hint (e.g. ``"Mathematics"``).
        context:
            Additional routing context (memory state, recent history,
            etc.).

        Returns
        -------
        RoutingDecision
            Routing information only — no teacher is invoked here.
        """
        self.ensure_teachers_loaded()

        available = list_teachers()
        candidates: List[str] = []

        # Score each teacher by keyword match, subject match, and
        # curriculum coverage.
        scored: List[tuple[int, str]] = []
        for tid in available:
            cls = get_teacher(tid)
            if cls is None:
                continue
            score = 0
            try:
                # Instantiate minimally to inspect metadata.
                instance = cls(
                    teacher_id=tid,
                    subject=tid,
                    display_name=tid,
                )
                req_lower = student_request.lower()

                # 1. Subject hint match (explicit subject parameter)
                if subject and instance.subject.lower() == subject.lower():
                    score += 20

                # 2. Keyword match against teacher keywords
                teacher_keywords = instance.get_keywords()
                keyword_matches = sum(
                    1 for kw in teacher_keywords if kw.lower() in req_lower
                )
                score += keyword_matches * 3

                # 3. Curriculum topic match
                for topic in instance.supported_curriculum:
                    if topic.lower() in req_lower:
                        score += 2
            except Exception:
                # If a teacher can't be instantiated, skip it.
                continue
            scored.append((score, tid))

        # Sort by score descending.
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [tid for _, tid in scored]

        # Determine primary teacher.
        primary_id: Optional[str] = candidates[0] if candidates else None

        # Multi-teacher detection: if the request mentions keywords
        # for multiple distinct subjects, flag it.
        mentioned: List[str] = self._detect_subjects(
            student_request, available
        )

        decision = RoutingDecision(
            teacher_id=primary_id,
            candidate_teachers=candidates,
        )

        if subject is None:
            if len(mentioned) > 1:
                decision.requires_multiple_teachers = True
                decision.reasoning = (
                    f"Request spans multiple subjects: "
                    f"{', '.join(mentioned)}. "
                    "Consider multi-teacher orchestration."
                )
                # Identify the secondary teacher for handoff preparation.
                # The secondary teacher is the one whose subject appears
                # in the request but is not the primary.
                for tid in mentioned:
                    if tid != primary_id:
                        decision.requested_teacher_id = tid
                        break
            else:
                decision.reasoning = (
                    f"Single-teacher route to "
                    f"{decision.teacher_id or 'none'}."
                )
        else:
            decision.reasoning = (
                f"Subject hint '{subject}' -> teacher "
                f"{decision.teacher_id or 'none'}."
            )

        # --- Tool requirement heuristic ---
        tool_keywords = (
            "draw", "diagram", "equation", "graph", "plot",
            "whiteboard", "sketch", "solve", "calculate",
        )
        req_lower = student_request.lower()
        if any(kw in req_lower for kw in tool_keywords):
            decision.requires_tool = True
            if decision.reasoning:
                decision.reasoning += " Tool likely required."
            else:
                decision.reasoning = "Tool likely required."

        return decision

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_subjects(
        request: str,
        available_teachers: List[str],
    ) -> List[str]:
        """Return teacher IDs whose keywords appear in *request*.

        Uses each teacher's registered keywords (from config.json) for
        detection, falling back to subject name matching.
        """
        found: List[str] = []
        req_lower = request.lower()
        for tid in available_teachers:
            cls = get_teacher(tid)
            if cls is None:
                continue
            try:
                instance = cls(
                    teacher_id=tid,
                    subject=tid,
                    display_name=tid,
                )
                # Check keywords first.
                keywords = instance.get_keywords()
                if any(kw.lower() in req_lower for kw in keywords):
                    found.append(tid)
                    continue
                # Fallback: subject name match.
                if instance.subject.lower() in req_lower:
                    found.append(tid)
            except Exception:
                continue
        return found

    def get_teacher_class(self, teacher_id: str) -> Optional[type]:
        """Return the :class:`Teacher` class for *teacher_id*, or None."""
        self.ensure_teachers_loaded()
        return get_teacher(teacher_id)
