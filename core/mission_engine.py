"""AI School OS — Phase 4.3 Mission Engine.

Handles daily missions, lesson missions, XP milestones, completion
percentage, and unlock status.  Pure backend logic — no UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class MissionProgress:
    """Progress toward a mission.

    Attributes
    ----------
    mission_id:
        Unique identifier for the mission.
    title:
        Human-readable mission title.
    description:
        What the mission entails.
    total_lessons:
        Total number of lessons in the mission.
    completed_lessons:
        Number of lessons completed.
    progress_percent:
        Completion percentage (0 to 100).
    completed:
        Whether the mission is fully complete.
    remaining:
        Lessons left to complete.
    xp_milestone:
        XP awarded on completion, or ``None``.
    unlocked:
        Whether the mission is currently available to start.
    unlock_condition:
        Description of what is needed to unlock this mission.
    """

    mission_id: str
    title: str
    description: str
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    completed: bool
    remaining: int
    xp_milestone: Optional[int]
    unlocked: bool
    unlock_condition: str


@dataclass
class XPMilestone:
    """An XP milestone definition.

    Attributes
    ----------
    level:
        The student level this milestone corresponds to.
    xp_required:
        Total XP required to reach this level.
    reward:
        Description of the reward/unlock.
    """

    level: int
    xp_required: int
    reward: str


class MissionEngine:
    """Manages missions, lesson progress, and XP milestones.

    Pure logic — reads and writes through an injected
    :class:`Memory` instance.
    """

    # ------------------------------------------------------------------
    # Default XP milestones (level -> required XP)
    # ------------------------------------------------------------------
    DEFAULT_MILESTONES: List[XPMilestone] = [
        XPMilestone(level=1, xp_required=0, reward="Welcome to AI School OS"),
        XPMilestone(level=2, xp_required=1000, reward="First steps badge"),
        XPMilestone(level=3, xp_required=3000, reward="Dedicated learner badge"),
        XPMilestone(level=4, xp_required=6000, reward="Subject explorer badge"),
        XPMilestone(level=5, xp_required=10000, reward="Consistent student badge"),
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def compute_progress(
        self,
        lessons_total: int,
        lessons_completed: int,
    ) -> Dict[str, Any]:
        """Compute mission progress from raw counts.

        Parameters
        ----------
        lessons_total:
            Total lessons in the mission.
        lessons_completed:
            Lessons completed so far.

        Returns
        -------
        dict
            Keys: ``progress_percent``, ``completed``, ``remaining``.
        """
        if lessons_total <= 0:
            return {
                "progress_percent": 0.0,
                "completed": False,
                "remaining": 0,
            }
        percent = round((lessons_completed / lessons_total) * 100, 1)
        return {
            "progress_percent": min(100.0, max(0.0, percent)),
            "completed": lessons_completed >= lessons_total,
            "remaining": max(0, lessons_total - lessons_completed),
        }

    def build_mission(
        self,
        mission_id: str,
        title: str,
        description: str,
        lessons_total: int,
        lessons_completed: int,
        xp_milestone: Optional[int] = None,
        unlocked: bool = True,
        unlock_condition: str = "Available from the start",
    ) -> MissionProgress:
        """Build a :class:`MissionProgress` from raw data.

        Parameters
        ----------
        mission_id:
            Unique mission identifier.
        title:
            Mission title.
        description:
            Mission description.
        lessons_total:
            Total lessons in the mission.
        lessons_completed:
            Lessons completed.
        xp_milestone:
            XP awarded on completion.
        unlocked:
            Whether the mission is unlocked.
        unlock_condition:
            Condition required to unlock the mission.

        Returns
        -------
        MissionProgress
        """
        progress = self.compute_progress(lessons_total, lessons_completed)
        return MissionProgress(
            mission_id=mission_id,
            title=title,
            description=description,
            total_lessons=lessons_total,
            completed_lessons=lessons_completed,
            progress_percent=progress["progress_percent"],
            completed=progress["completed"],
            remaining=progress["remaining"],
            xp_milestone=xp_milestone,
            unlocked=unlocked,
            unlock_condition=unlock_condition,
        )

    def compute_level_from_xp(
        self,
        xp: int,
        milestones: Optional[List[XPMilestone]] = None,
    ) -> int:
        """Compute the student's level from total XP.

        Parameters
        ----------
        xp:
            Total earned XP.
        milestones:
            Optional list of milestones.  Defaults to
            :attr:`DEFAULT_MILESTONES`.

        Returns
        -------
        int
            The student's current level (at least 1).
        """
        milestones = milestones or self.DEFAULT_MILESTONES
        level = 1
        for m in sorted(milestones, key=lambda x: x.xp_required):
            if xp >= m.xp_required:
                level = m.level
        return level

    def next_milestone(
        self,
        xp: int,
        milestones: Optional[List[XPMilestone]] = None,
    ) -> Optional[XPMilestone]:
        """Return the next unachieved XP milestone, or ``None``."""
        milestones = milestones or self.DEFAULT_MILESTONES
        for m in sorted(milestones, key=lambda x: x.xp_required):
            if xp < m.xp_required:
                return m
        return None

    def daily_mission(
        self,
        student_id: int,
        subject: str,
    ) -> MissionProgress:
        """Generate a simple daily mission for a student.

        This is a deterministic placeholder that future phases can
        replace with dynamic mission generation.

        Parameters
        ----------
        student_id:
            The student.
        subject:
            The subject for the mission.

        Returns
        -------
        MissionProgress
        """
        return self.build_mission(
            mission_id=f"daily_{student_id}_{date.today().isoformat()}",
            title=f"Daily {subject} Mission",
            description=f"Complete one {subject} lesson today.",
            lessons_total=1,
            lessons_completed=0,
            xp_milestone=25,
            unlocked=True,
            unlock_condition="Log in and start a lesson.",
        )
