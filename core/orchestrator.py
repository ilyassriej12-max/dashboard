"""AI School OS — Phase 4.1 central decision engine (orchestrator).

The orchestrator receives a student request and returns routing
information — which teacher should answer, whether multiple teachers
are required, and whether a tool will be needed later.

No LLM calls are made here.  No answers are generated.  This is
architecture only: the decision rules that Phase 4.2+ will refine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.loader import get_teacher, list_teachers
from core.teacher import Teacher


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
    """

    teacher_id: Optional[str]
    requires_multiple_teachers: bool = False
    requires_tool: bool = False
    reasoning: str = ""
    candidate_teachers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teacher_id": self.teacher_id,
            "requires_multiple_teachers": self.requires_multiple_teachers,
            "requires_tool": self.requires_tool,
            "reasoning": self.reasoning,
            "candidate_teachers": self.candidate_teachers,
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

    def __init__(self) -> None:
        self._teachers_loaded: bool = False

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def ensure_teachers_loaded(self) -> None:
        """Trigger plugin discovery if not yet done."""
        if not self._teachers_loaded:
            # Import here to avoid circular imports at module load time.
            from core.loader import load_teachers

            load_teachers()
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

        # Score each teacher by subject match and curriculum coverage.
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
                if subject and instance.subject.lower() == subject.lower():
                    score += 10
                # Check if any request keywords match curriculum topics.
                req_lower = student_request.lower()
                for topic in instance.supported_curriculum:
                    if topic.lower() in req_lower:
                        score += 5
            except Exception:
                # If a teacher can't be instantiated, skip it.
                continue
            scored.append((score, tid))

        # Sort by score descending.
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [tid for _, tid in scored]

        decision = RoutingDecision(
            teacher_id=candidates[0] if candidates else None,
            candidate_teachers=candidates,
        )

        # --- Multi-teacher heuristic ---
        # If the request mentions multiple distinct subjects, flag it.
        if subject is None:
            # Simple heuristic: look for subject keywords in the request.
            mentioned = self._detect_subjects(student_request, available)
            if len(mentioned) > 1:
                decision.requires_multiple_teachers = True
                decision.reasoning = (
                    f"Request spans multiple subjects: {', '.join(mentioned)}. "
                    "Consider multi-teacher orchestration."
                )
            else:
                decision.reasoning = (
                    f"Single-teacher route to {decision.teacher_id or 'none'}."
                )
        else:
            decision.reasoning = (
                f"Subject hint '{subject}' -> teacher {decision.teacher_id or 'none'}."
            )

        # --- Tool requirement heuristic ---
        # If the request mentions drawing, diagrams, equations, etc.,
        # anticipate a tool need.
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
        """Return teacher IDs whose subject name appears in *request*."""
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
                if instance.subject.lower() in req_lower:
                    found.append(tid)
            except Exception:
                continue
        return found

    def get_teacher_class(self, teacher_id: str) -> Optional[type]:
        """Return the :class:`Teacher` class for *teacher_id*, or None."""
        self.ensure_teachers_loaded()
        return get_teacher(teacher_id)
