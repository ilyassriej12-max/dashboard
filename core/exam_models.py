"""AI School OS — Phase 5.4 Exam Models.

Data models for exams, questions, answers, scores, and rubrics.
Supports Homework, Quiz, Exam, and Bac Simulation modes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ExamQuestion:
    """A single exam question."""

    id: str
    question: str
    subject: str
    chapter: str
    lesson: str
    competency: str
    difficulty: str  # beginner, easy, medium, advanced, expert
    question_type: str  # multiple_choice, short_answer, essay, problem_solving
    points: int
    correct_answer: str
    explanation: str
    language: str = "darija"  # darija, french, arabic, english, mixed


@dataclass
class ExamAttempt:
    """A single student attempt at answering a question."""

    question_id: str
    student_answer: str
    is_correct: bool
    points_earned: float
    max_points: int
    feedback: str
    timestamp: str = field(default_factory=lambda: str(__import__("datetime").datetime.now()))


@dataclass
class ExamResult:
    """The complete result of an exam attempt."""

    exam_id: str
    student_id: int
    teacher_id: str
    subject: str
    exam_type: str  # homework, quiz, exam, bac_simulation
    total_score: float
    max_score: int
    percentage: float
    grade: str  # A, B, C, D, F or equivalent
    passed: bool
    time_spent_minutes: int
    questions: List[ExamAttempt]
    started_at: str
    completed_at: str
    feedback: str
    recommendations: List[str] = field(default_factory=list)
    barème: str = ""  # grading rubric in French/Moroccan style


@dataclass
class ExamTemplate:
    """Template for generating exams."""

    exam_id: str
    title: str
    subject: str
    chapter_id: str
    lesson_id: str
    competency: str
    exam_type: str  # homework, quiz, exam, bac_simulation
    difficulty: str
    num_questions: int
    time_limit_minutes: int
    total_points: int
    passing_score: int
    language: str = "darija"
    barème: str = ""  # grading rubric