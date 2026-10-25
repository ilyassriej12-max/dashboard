"""AI School OS — Phase 3B Pydantic schemas.

Request/response shapes for the REST API. All responses return JSON only.
Python field names use snake_case; JSON keys use camelCase (via alias
generation) so the frontend receives the casing it expects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: snake_case attributes, camelCase JSON keys."""
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------
class MessageResponse(CamelModel):
    ok: bool = True
    message: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardStats(CamelModel):
    weekly_xp: int = Field(alias="weeklyXP")
    weekly_time: int  # minutes
    mastery: int
    exercises_completed: int
    completion_rate: int
    weekly_goal_progress: int  # percent (5 of 7 days)
    current_subject_id: str


class DashboardResponse(CamelModel):
    stats: DashboardStats
    subjects: List[dict]


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------
class Subject(CamelModel):
    id: str
    icon: Optional[str] = None
    name: str
    description: Optional[str] = None
    progress: int
    color: Optional[str] = None
    teacher: Optional[str] = None
    next_session: Optional[str] = None
    lessons: Optional[int] = None
    mastery: Optional[int] = None
    streak: Optional[int] = None
    difficulty: Optional[str] = None
    last_lesson: Optional[str] = None


# ---------------------------------------------------------------------------
# Teachers
# ---------------------------------------------------------------------------
class Teacher(CamelModel):
    id: str
    name: str
    specialty: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    rating: Optional[float] = None
    next_session: Optional[str] = None


# ---------------------------------------------------------------------------
# Homework
# ---------------------------------------------------------------------------
class Homework(CamelModel):
    id: str
    subject_id: Optional[str] = None
    subject: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[int] = None
    completed_problems: Optional[int] = None
    total_problems: Optional[int] = None
    estimated_time: Optional[int] = None


class HomeworkCompleteRequest(CamelModel):
    id: str


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
class CalendarEvent(CamelModel):
    id: str
    date: str
    title: str
    type: Optional[str] = None
    subject_id: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = None


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
class Profile(CamelModel):
    id: int = 1
    name: str
    avatar: str
    cohort: str
    semester: int
    joined_date: str
    level: int
    xp: int
    xp_to_next_level: int
    streak: int
    total_study_time: int
    mastery: int
    preferences: dict = {}


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
class SettingItem(CamelModel):
    key: str
    value: str


class SettingsRequest(CamelModel):
    key: str
    value: str


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class Notification(CamelModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    timestamp: int


# ---------------------------------------------------------------------------
# Notes / messages
# ---------------------------------------------------------------------------
class NotesRequest(CamelModel):
    content: str


# ---------------------------------------------------------------------------
# Progress / lessons (subject page metric cards + history)
# ---------------------------------------------------------------------------
class ProgressItem(CamelModel):
    subject_id: str
    label: str
    value: int
    unit: str


class LessonItem(CamelModel):
    id: int
    subject_id: Optional[str] = None
    name: str
    date: Optional[str] = None
    tag: Optional[str] = None
    duration: Optional[str] = None
    score: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Chat (AI Foundation - Phase 4.2)
# ---------------------------------------------------------------------------
class ChatRequest(CamelModel):
    message: str
    teacher: str  # teacher_id
    student: int  # student_id
    curriculum: Optional[str] = None


class ChatResponse(CamelModel):
    answer: str
    teacher: str
    provider: str
    model: str
    timestamp: int
    tokens: Optional[int] = None

