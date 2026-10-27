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


# ---------------------------------------------------------------------------
# Phase 5.6: Homework
# ---------------------------------------------------------------------------
class HomeworkGenerateRequest(CamelModel):
    student_id: int
    subject_id: str
    chapter_id: str
    lesson_id: str
    competency: str
    num_questions: int = 5
    difficulty: str = "medium"


class HomeworkGenerateResponse(CamelModel):
    homework_id: str
    title: str
    subject: str
    chapter_id: str
    lesson_id: str
    competency: str
    difficulty: str
    num_questions: int
    time_limit_minutes: int
    total_points: int
    due_date: Optional[str] = None
    estimated_time: Optional[int] = None
    questions: List[dict]


class HomeworkSubmitRequest(CamelModel):
    student_id: int
    homework_id: str
    answers: Dict[str, str]  # question_id -> answer text
    time_spent_minutes: int = 0


class HomeworkSubmitResponse(CamelModel):
    homework_id: str
    student_id: int
    total_score: float
    max_score: int
    percentage: float
    grade: str
    passed: bool
    time_spent_minutes: int
    feedback: str
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Phase 5.6: Quiz
# ---------------------------------------------------------------------------
class QuizGenerateRequest(CamelModel):
    student_id: int
    subject_id: str
    chapter_id: str
    lesson_id: str
    competency: str
    num_questions: int = 10
    difficulty: str = "medium"


class QuizGenerateResponse(CamelModel):
    quiz_id: str
    title: str
    subject: str
    chapter_id: str
    lesson_id: str
    competency: str
    difficulty: str
    num_questions: int
    time_limit_minutes: int
    total_points: int
    questions: List[dict]


class QuizSubmitRequest(CamelModel):
    student_id: int
    quiz_id: str
    answers: Dict[str, str]
    time_spent_minutes: int = 0


class QuizSubmitResponse(CamelModel):
    quiz_id: str
    student_id: int
    total_score: float
    max_score: int
    percentage: float
    grade: str
    passed: bool
    time_spent_minutes: int
    feedback: str
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Phase 5.6: Exam
# ---------------------------------------------------------------------------
class ExamGenerateRequest(CamelModel):
    student_id: int
    subject_id: str
    chapter_id: str
    lesson_id: str
    competency: str
    exam_type: str = "practice"  # practice, chapter, semester, regional, bac_simulation
    num_questions: int = 20
    difficulty: str = "advanced"


class ExamGenerateResponse(CamelModel):
    exam_id: str
    title: str
    subject: str
    chapter_id: str
    lesson_id: str
    competency: str
    exam_type: str
    difficulty: str
    num_questions: int
    time_limit_minutes: int
    total_points: int
    questions: List[dict]


class ExamSubmitRequest(CamelModel):
    student_id: int
    exam_id: str
    answers: Dict[str, str]
    time_spent_minutes: int = 0


class ExamSubmitResponse(CamelModel):
    exam_id: str
    student_id: int
    exam_type: str
    total_score: float
    max_score: int
    percentage: float
    grade: str
    passed: bool
    time_spent_minutes: int
    feedback: str
    recommendations: List[str]
    barème: str
    competency_analysis: List[dict]
    mistake_summary: List[dict]


# ---------------------------------------------------------------------------
# Phase 5.6: Timeline
# ---------------------------------------------------------------------------
class TimelineEvent(CamelModel):
    id: int
    student_id: int
    event_type: str
    subject_id: Optional[str] = None
    lesson_id: Optional[str] = None
    chapter_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    score: Optional[float] = None
    timestamp: int


# ---------------------------------------------------------------------------
# Phase 5.6: Learning Statistics
# ---------------------------------------------------------------------------
class LearningStatistic(CamelModel):
    id: int
    student_id: int
    period_type: str
    period_start: str
    period_end: str
    total_study_time_minutes: int
    lessons_completed: int
    quizzes_taken: int
    exams_taken: int
    average_quiz_score: Optional[float] = None
    average_exam_score: Optional[float] = None
    completion_rate: float
    subject_id: Optional[str] = None
    updated_at: int

