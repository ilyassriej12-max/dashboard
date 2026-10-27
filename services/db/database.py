"""AI School OS — Phase 3B database layer.

SQLite connection, schema initialization, and seed data.
Seed data mirrors the Phase 3A frontend mock data exactly so the UI
remains pixel-perfect and behaviour-identical.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Resolve the database file next to this module: services/db/ai_school.db
_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(_DIR, "ai_school.db")
SCHEMA_PATH = os.path.join(_DIR, "schema.sql")


def get_conn() -> sqlite3.Connection:
    """Open a sqlite3 connection with row factory and foreign keys on."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables from schema.sql and seed demo data if tables are empty."""
    conn = get_conn()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        # Schema migrations: add new columns to existing tables if missing.
        _migrate_schema(conn)

        # Seed only when tables are empty (idempotent).
        if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            _seed(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate_schema(conn) -> None:
    """Add missing columns to existing tables for schema migration."""
    migrations = [
        ("homework_attempts", "homework_id TEXT NOT NULL UNIQUE DEFAULT ''"),
        ("quiz_attempts", "quiz_id TEXT NOT NULL UNIQUE DEFAULT ''"),
        ("exam_attempts", "exam_id TEXT NOT NULL UNIQUE DEFAULT ''"),
    ]
    for table, column_def in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        except Exception:
            # Column already exists or table doesn't exist yet - skip.
            pass


def _seed(conn: sqlite3.Connection) -> None:
    """Insert Phase 3A-equivalent demo data."""

    # ---- students ----
    conn.execute(
        """
        INSERT INTO students
        (id, name, avatar, cohort, semester, joined_date, level, xp,
         xp_to_next_level, streak, total_study_time, mastery,
         weekly_xp, weekly_time, exercises_completed, completion_rate,
         weekly_goal_progress, current_subject_id,
         theme, language, animations, reduced_motion, captions,
         focus_mode, lesson_reminders)
        VALUES (1, 'Alex Rivera', 'AR', 'Turing', 2, '2026-09-01', 18, 18420,
                2180, 24, 2538, 84, 4820, 342, 128, 91, 72,
                'mathematics', 'dark', 'en', 1, 0, 1, 0, 1)
        """
    )

    # ---- subjects (matches frontend mock subjects array) ----
    subjects: List[Dict[str, Any]] = [
        {
            "id": "mathematics", "icon": "\u2211", "name": "Mathematics",
            "description": "Calculus · Algebra", "progress": 62,
            "color": "var(--primary)", "teacher": "Dr. Ada",
            "next_session": "16:30", "lessons": 58, "mastery": 84,
            "streak": 12, "difficulty": "Advanced",
            "last_lesson": "Integration by Parts · Part 2",
        },
        {
            "id": "physics", "icon": "\u269b", "name": "Physics",
            "description": "Mechanics · Waves", "progress": 47,
            "color": "var(--primary-soft)", "teacher": "Prof. Newton",
            "next_session": "14:00", "lessons": 42, "mastery": 71,
            "streak": 8, "difficulty": "Intermediate",
            "last_lesson": "Wave Motion",
        },
        {
            "id": "chemistry", "icon": "🧪", "name": "Chemistry",
            "description": "Organic · Bonds", "progress": 54,
            "color": "var(--secondary)", "teacher": "Dr. Curie",
            "next_session": "10:30", "lessons": 36, "mastery": 68,
            "streak": 5, "difficulty": "Intermediate",
            "last_lesson": "Molecular Bonds",
        },
        {
            "id": "programming", "icon": "💻", "name": "Programming",
            "description": "Algorithms · Python", "progress": 78,
            "color": "var(--accent)", "teacher": "Prof. Turing",
            "next_session": "18:00", "lessons": 64, "mastery": 91,
            "streak": 24, "difficulty": "Advanced",
            "last_lesson": "Binary Search",
        },
        {
            "id": "biology", "icon": "🧬", "name": "Biology",
            "description": "Genetics · Cells", "progress": 41,
            "color": "var(--success)", "teacher": "Dr. Darwin",
            "next_session": "11:00", "lessons": 48, "mastery": 63,
            "streak": 3, "difficulty": "Beginner",
            "last_lesson": "Cell Division",
        },
        {
            "id": "geography", "icon": "🌍", "name": "Geography",
            "description": "Climate · Mapping", "progress": 66,
            "color": "var(--warning)", "teacher": "Prof. Humboldt",
            "next_session": "09:00", "lessons": 28, "mastery": 79,
            "streak": 7, "difficulty": "Intermediate",
            "last_lesson": "Climate Patterns",
        },
        {
            "id": "literature", "icon": "📖", "name": "Literature",
            "description": "Modernism · Poetry", "progress": 33,
            "color": "var(--secondary)", "teacher": "Prof. Woolf",
            "next_session": "15:30", "lessons": 32, "mastery": 57,
            "streak": 2, "difficulty": "Beginner",
            "last_lesson": "Modernist Poetry",
        },
        {
            "id": "english", "icon": "🇬🇧", "name": "English",
            "description": "Writing · Analysis", "progress": 71,
            "color": "var(--primary)", "teacher": "Dr. Austen",
            "next_session": "13:00", "lessons": 40, "mastery": 82,
            "streak": 14, "difficulty": "Advanced",
            "last_lesson": "Essay Writing",
        },
        {
            "id": "french", "icon": "🇫🇷", "name": "French",
            "description": "Grammar · Listening", "progress": 29,
            "color": "var(--accent)", "teacher": "M. Proust",
            "next_session": "16:00", "lessons": 35, "mastery": 48,
            "streak": 1, "difficulty": "Beginner",
            "last_lesson": "Basic Grammar",
        },
        {
            "id": "history", "icon": "📜", "name": "History",
            "description": "Modern era · Sources", "progress": 58,
            "color": "var(--warning)", "teacher": "Prof. Braudel",
            "next_session": "10:00", "lessons": 45, "mastery": 73,
            "streak": 6, "difficulty": "Intermediate",
            "last_lesson": "Modern Era",
        },
    ]
    for s in subjects:
        conn.execute(
            """
            INSERT INTO subjects
            (id, icon, name, description, progress, color, teacher,
             next_session, lessons, mastery, streak, difficulty, last_lesson)
            VALUES (:id, :icon, :name, :description, :progress, :color,
                    :teacher, :next_session, :lessons, :mastery, :streak,
                    :difficulty, :last_lesson)
            """,
            s,
        )

    # ---- progress (subject page metric cards) ----
    progress_rows = [
        ("mathematics", "Progress", 62, "%"),
        ("mathematics", "Mastery", 84, "%"),
        ("mathematics", "Lessons done", 36, " / 58"),
        ("mathematics", "Avg. practice", 14, " min"),
    ]
    for subject_id, label, value, unit in progress_rows:
        conn.execute(
            "INSERT INTO progress (subject_id, label, value, unit) VALUES (?, ?, ?, ?)",
            (subject_id, label, value, unit),
        )

    # ---- teachers (matches frontend mock teachers array) ----
    teachers: List[Dict[str, Any]] = [
        {
            "id": "ada", "name": "Dr. Ada",
            "specialty": "Mathematics · AI Mentor", "status": "Available",
            "description": "Adaptive calculus sessions with real-time difficulty adjustment.",
            "avatar": "AA", "rating": 4.9, "next_session": "Today · 16:30",
        },
        {
            "id": "turing", "name": "Prof. Turing",
            "specialty": "Programming · AI Mentor", "status": "Available",
            "description": "Algorithms studio with hands-on coding challenges.",
            "avatar": "AT", "rating": 4.8, "next_session": "Tomorrow · 18:00",
        },
        {
            "id": "curie", "name": "Dr. Curie",
            "specialty": "Chemistry · Human Teacher", "status": "Busy",
            "description": "Office hours available Wednesdays 15:30.",
            "avatar": "MC", "rating": 4.9, "next_session": "Wed · 15:30",
        },
        {
            "id": "newton", "name": "Prof. Newton",
            "specialty": "Physics · Human Teacher", "status": "Available",
            "description": "Mechanics and waves with interactive simulations.",
            "avatar": "PN", "rating": 4.7, "next_session": "Today · 14:00",
        },
        {
            "id": "darwin", "name": "Dr. Darwin",
            "specialty": "Biology · Human Teacher", "status": "Available",
            "description": "Genetics and cell biology with virtual labs.",
            "avatar": "DD", "rating": 4.8, "next_session": "Today · 11:00",
        },
        {
            "id": "humboldt", "name": "Prof. Humboldt",
            "specialty": "Geography · Human Teacher", "status": "Available",
            "description": "Climate science and mapping with real-world data.",
            "avatar": "PH", "rating": 4.6, "next_session": "Today · 09:00",
        },
    ]
    for t in teachers:
        conn.execute(
            """
            INSERT INTO teachers
            (id, name, specialty, status, description, avatar, rating, next_session)
            VALUES (:id, :name, :specialty, :status, :description, :avatar,
                    :rating, :next_session)
            """,
            t,
        )

    # ---- homework (matches frontend mock homework array) ----
    homework: List[Dict[str, Any]] = [
        {
            "id": "hw1", "subject_id": "mathematics", "subject": "Mathematics",
            "title": "Integration by Parts — Set 4",
            "description": "8 problems covering integration by parts technique",
            "due_date": "2026-10-10T20:00:00", "status": "in-progress",
            "priority": "high", "progress": 63, "completed_problems": 5,
            "total_problems": 8, "estimated_time": 18,
        },
        {
            "id": "hw2", "subject_id": "physics", "subject": "Physics",
            "title": "Wave Motion Reflection",
            "description": "Reflection essay on wave behavior in different media",
            "due_date": "2026-10-11T23:59:00", "status": "pending",
            "priority": "medium", "progress": 0, "completed_problems": 0,
            "total_problems": 1, "estimated_time": 45,
        },
        {
            "id": "hw3", "subject_id": "programming", "subject": "Programming",
            "title": "Binary Search Walkthrough",
            "description": "Implement and document binary search algorithm",
            "due_date": "2026-10-09T18:00:00", "status": "completed",
            "priority": "high", "progress": 100, "completed_problems": 1,
            "total_problems": 1, "estimated_time": 60,
        },
        {
            "id": "hw4", "subject_id": "chemistry", "subject": "Chemistry",
            "title": "Molecular Bonds Map",
            "description": "Create concept map of molecular bond types",
            "due_date": "2026-10-13T20:00:00", "status": "pending",
            "priority": "low", "progress": 25, "completed_problems": 1,
            "total_problems": 4, "estimated_time": 30,
        },
        {
            "id": "hw5", "subject_id": "literature", "subject": "Literature",
            "title": "Modernist Poetry Analysis",
            "description": "Analyze three modernist poems",
            "due_date": "2026-10-12T15:00:00", "status": "in-progress",
            "priority": "medium", "progress": 40, "completed_problems": 2,
            "total_problems": 5, "estimated_time": 40,
        },
    ]
    for h in homework:
        conn.execute(
            """
            INSERT INTO homework
            (id, subject_id, subject, title, description, due_date, status,
             priority, progress, completed_problems, total_problems,
             estimated_time)
            VALUES (:id, :subject_id, :subject, :title, :description,
                    :due_date, :status, :priority, :progress,
                    :completed_problems, :total_problems, :estimated_time)
            """,
            h,
        )

    # ---- notifications (matches frontend mock notifications array) ----
    import time as _time
    now = int(_time.time() * 1000)
    notifications: List[Dict[str, Any]] = [
        {
            "id": "notif1", "type": "board",
            "title": "Your Mathematics lesson starts in 30 minutes",
            "message": "Integration by Parts · 16:30", "read": 0,
            "timestamp": now - 30 * 60 * 1000,
        },
        {
            "id": "notif2", "type": "homework",
            "title": "Set 4 is due today",
            "message": "You have 3 problems left · due 20:00", "read": 0,
            "timestamp": now - 60 * 60 * 1000,
        },
        {
            "id": "notif3", "type": "spark",
            "title": "A practice hint is ready",
            "message": "The AI tutor noticed a repeated error pattern.",
            "read": 0, "timestamp": now - 2 * 60 * 60 * 1000,
        },
        {
            "id": "notif4", "type": "check",
            "title": "Checkpoint feedback arrived",
            "message": "You scored 92% on Substitution Deep Dive.", "read": 1,
            "timestamp": now - 24 * 60 * 60 * 1000,
        },
        {
            "id": "notif5", "type": "book",
            "title": "A saved resource was updated",
            "message": "Calculus formula notebook · new examples added",
            "read": 1, "timestamp": now - 48 * 60 * 60 * 1000,
        },
    ]
    for n in notifications:
        conn.execute(
            """
            INSERT INTO notifications
            (id, type, title, message, read, timestamp)
            VALUES (:id, :type, :title, :message, :read, :timestamp)
            """,
            n,
        )

    # ---- calendar (matches frontend mock calendarEvents array) ----
    calendar_events: List[Dict[str, Any]] = [
        {"id": "evt1", "date": "2026-10-10", "title": "Calculus Lesson",
         "type": "lesson", "subject_id": "mathematics", "time": "16:30",
         "duration": 45},
        {"id": "evt2", "date": "2026-10-10", "title": "Set 4 Due",
         "type": "deadline", "subject_id": "mathematics", "time": "20:00",
         "duration": None},
        {"id": "evt3", "date": "2026-10-11", "title": "Physics Lab",
         "type": "lesson", "subject_id": "physics", "time": "14:00",
         "duration": 60},
        {"id": "evt4", "date": "2026-10-12", "title": "Literature Discussion",
         "type": "lesson", "subject_id": "literature", "time": "15:30",
         "duration": 45},
        {"id": "evt5", "date": "2026-10-13", "title": "Chemistry Lab",
         "type": "lesson", "subject_id": "chemistry", "time": "10:30",
         "duration": 90},
        {"id": "evt6", "date": "2026-10-14", "title": "Programming Workshop",
         "type": "lesson", "subject_id": "programming", "time": "18:00",
         "duration": 120},
        {"id": "evt7", "date": "2026-10-15", "title": "Checkpoint Quiz",
         "type": "deadline", "subject_id": "mathematics", "time": "16:30",
         "duration": None},
        {"id": "evt8", "date": "2026-10-16", "title": "Biology Review",
         "type": "lesson", "subject_id": "biology", "time": "11:00",
         "duration": 60},
        {"id": "evt9", "date": "2026-10-17", "title": "Geography Mapping",
         "type": "lesson", "subject_id": "geography", "time": "09:00",
         "duration": 45},
        {"id": "evt10", "date": "2026-10-18", "title": "Midterm Checkpoint",
         "type": "deadline", "subject_id": "mathematics", "time": "16:30",
         "duration": None},
    ]
    for e in calendar_events:
        conn.execute(
            """
            INSERT INTO calendar
            (id, date, title, type, subject_id, time, duration)
            VALUES (:id, :date, :title, :type, :subject_id, :time,
                    :duration)
            """,
            e,
        )

    # ---- settings ----
    settings_rows = [
        ("theme", "dark"),
        ("language", "en"),
        ("animations", "true"),
        ("reducedMotion", "false"),
        ("captions", "true"),
        ("focusMode", "false"),
        ("lessonReminders", "true"),
    ]
    for key, value in settings_rows:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?)", (key, value)
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Phase 5.6: Lesson Progress persistence helpers
# ---------------------------------------------------------------------------
def save_lesson_progress(
    student_id: int,
    subject_id: str,
    lesson_id: str,
    status: Optional[str] = None,
    attempts: Optional[int] = None,
    time_spent_minutes: Optional[int] = None,
    best_score: Optional[float] = None,
    last_attempt_at: Optional[int] = None,
    completed_at: Optional[int] = None,
) -> None:
    """Upsert lesson progress for a student."""
    import time as _time
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT id FROM lesson_progress
            WHERE student_id = ? AND subject_id = ? AND lesson_id = ?
            """,
            (student_id, subject_id, lesson_id),
        ).fetchone()
        now = int(_time.time() * 1000)
        if row is None:
            conn.execute(
                """
                INSERT INTO lesson_progress
                (student_id, subject_id, lesson_id, status, attempts,
                 time_spent_minutes, best_score, last_attempt_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id, subject_id, lesson_id,
                    status or "not_started",
                    attempts or 0,
                    time_spent_minutes or 0,
                    best_score,
                    last_attempt_at or now,
                    completed_at,
                ),
            )
        else:
            updates = []
            params: List[Any] = []
            if status is not None:
                updates.append("status = ?"); params.append(status)
            if attempts is not None:
                updates.append("attempts = ?"); params.append(attempts)
            if time_spent_minutes is not None:
                updates.append("time_spent_minutes = time_spent_minutes + ?"); params.append(time_spent_minutes)
            if best_score is not None:
                updates.append("best_score = MAX(best_score, ?)"); params.append(best_score)
            if last_attempt_at is not None:
                updates.append("last_attempt_at = ?"); params.append(last_attempt_at)
            if completed_at is not None:
                updates.append("completed_at = ?"); params.append(completed_at)
            if updates:
                params.extend([student_id, subject_id, lesson_id])
                conn.execute(
                    f"UPDATE lesson_progress SET {', '.join(updates)} "
                    "WHERE student_id = ? AND subject_id = ? AND lesson_id = ?",
                    params,
                )
        conn.commit()
    finally:
        conn.close()


def load_lesson_progress(
    student_id: int,
    subject_id: str,
    lesson_id: str,
) -> Optional[Dict[str, Any]]:
    """Load lesson progress for a specific lesson."""
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT * FROM lesson_progress
            WHERE student_id = ? AND subject_id = ? AND lesson_id = ?
            """,
            (student_id, subject_id, lesson_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def load_all_lesson_progress(
    student_id: int,
    subject_id: str,
) -> List[Dict[str, Any]]:
    """Load all lesson progress for a student in a subject."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM lesson_progress
            WHERE student_id = ? AND subject_id = ?
            """,
            (student_id, subject_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_all_student_lesson_progress(
    student_id: int,
) -> Dict[str, List[Dict[str, Any]]]:
    """Load all lesson progress for a student across all subjects."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM lesson_progress
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchall()
        result: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            d = dict(r)
            result.setdefault(d["subject_id"], []).append(d)
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Competency Mastery persistence helpers
# ---------------------------------------------------------------------------
def save_competency_mastery(
    student_id: int,
    subject_id: str,
    competency_id: str,
    score: float,
    times_assessed: Optional[int] = None,
) -> None:
    """Upsert competency mastery for a student."""
    import time as _time
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT id, score, times_assessed FROM competency_mastery
            WHERE student_id = ? AND subject_id = ? AND competency_id = ?
            """,
            (student_id, subject_id, competency_id),
        ).fetchone()
        now = int(_time.time() * 1000)
        if row is None:
            conn.execute(
                """
                INSERT INTO competency_mastery
                (student_id, subject_id, competency_id, score, updated_at, times_assessed)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (student_id, subject_id, competency_id, score, now, times_assessed or 1),
            )
        else:
            existing_score = row["score"]
            existing_assessed = row["times_assessed"]
            new_assessed = (existing_assessed or 0) + (times_assessed or 0)
            conn.execute(
                """
                UPDATE competency_mastery
                SET score = ?, updated_at = ?, times_assessed = ?
                WHERE id = ?
                """,
                (score, now, new_assessed, row["id"]),
            )
        conn.commit()
    finally:
        conn.close()


def load_competency_mastery(
    student_id: int,
    subject_id: str,
    competency_id: str,
) -> Optional[Dict[str, Any]]:
    """Load competency mastery for a specific competency."""
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT * FROM competency_mastery
            WHERE student_id = ? AND subject_id = ? AND competency_id = ?
            """,
            (student_id, subject_id, competency_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def load_all_competency_mastery(
    student_id: int,
    subject_id: str,
) -> List[Dict[str, Any]]:
    """Load all competency mastery for a student in a subject."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM competency_mastery
            WHERE student_id = ? AND subject_id = ?
            """,
            (student_id, subject_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_all_student_competency_mastery(
    student_id: int,
) -> Dict[str, List[Dict[str, Any]]]:
    """Load all competency mastery for a student across all subjects."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM competency_mastery
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchall()
        result: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            d = dict(r)
            result.setdefault(d["subject_id"], []).append(d)
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Homework attempt persistence helpers
# ---------------------------------------------------------------------------
def save_homework_attempt(
    student_id: int,
    subject_id: str,
    chapter_id: Optional[str],
    lesson_id: Optional[str],
    competency: Optional[str],
    title: str,
    description: Optional[str],
    difficulty: Optional[str],
    due_date: Optional[str],
    estimated_time: Optional[int],
    status: str,
    score: Optional[float],
    total_score: Optional[float],
    percentage: Optional[float],
    created_at: Optional[int],
    completed_at: Optional[int],
    homework_id: Optional[str] = None,
) -> int:
    """Insert a homework attempt record and return its ID."""
    import time as _time
    conn = get_conn()
    try:
        now = int(_time.time() * 1000)
        cursor = conn.execute(
            """
            INSERT INTO homework_attempts
            (homework_id, student_id, subject_id, chapter_id, lesson_id, competency,
             title, description, difficulty, due_date, estimated_time,
             status, score, total_score, percentage, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                homework_id,
                student_id, subject_id, chapter_id, lesson_id, competency,
                title, description, difficulty, due_date, estimated_time,
                status, score, total_score, percentage,
                created_at or now, completed_at,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_homework_attempts(
    student_id: int,
) -> List[Dict[str, Any]]:
    """Load all homework attempts for a student."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM homework_attempts
            WHERE student_id = ?
            ORDER BY created_at DESC
            """,
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Quiz attempt persistence helpers
# ---------------------------------------------------------------------------
def save_quiz_attempt(
    student_id: int,
    subject_id: str,
    chapter_id: Optional[str],
    lesson_id: Optional[str],
    competency: Optional[str],
    title: str,
    difficulty: Optional[str],
    num_questions: int,
    score: float,
    total_score: float,
    percentage: float,
    grade: str,
    passed: bool,
    started_at: Optional[int],
    completed_at: Optional[int],
    quiz_id: Optional[str] = None,
) -> int:
    """Insert a quiz attempt record and return its ID."""
    import time as _time
    conn = get_conn()
    try:
        now = int(_time.time() * 1000)
        cursor = conn.execute(
            """
            INSERT INTO quiz_attempts
            (quiz_id, student_id, subject_id, chapter_id, lesson_id, competency,
             title, difficulty, num_questions, score, total_score,
             percentage, grade, passed, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quiz_id,
                student_id, subject_id, chapter_id, lesson_id, competency,
                title, difficulty, num_questions, score, total_score,
                percentage, grade, 1 if passed else 0,
                started_at or now, completed_at or now,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_quiz_attempts(
    student_id: int,
) -> List[Dict[str, Any]]:
    """Load all quiz attempts for a student."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM quiz_attempts
            WHERE student_id = ?
            ORDER BY started_at DESC
            """,
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Exam attempt persistence helpers
# ---------------------------------------------------------------------------
def save_exam_attempt(
    student_id: int,
    subject_id: str,
    chapter_id: Optional[str],
    lesson_id: Optional[str],
    competency: Optional[str],
    title: str,
    exam_type: str,
    difficulty: Optional[str],
    num_questions: int,
    score: float,
    total_score: float,
    percentage: float,
    grade: str,
    passed: bool,
    time_spent_minutes: int,
    started_at: Optional[int],
    completed_at: Optional[int],
    recommendations: Optional[str],
    barème: Optional[str],
    exam_id: Optional[str] = None,
) -> int:
    """Insert an exam attempt record and return its ID."""
    import time as _time
    conn = get_conn()
    try:
        now = int(_time.time() * 1000)
        cursor = conn.execute(
            """
            INSERT INTO exam_attempts
            (exam_id, student_id, subject_id, chapter_id, lesson_id, competency,
             title, exam_type, difficulty, num_questions, score, total_score,
             percentage, grade, passed, time_spent_minutes, started_at,
             completed_at, recommendations, barème)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exam_id,
                student_id, subject_id, chapter_id, lesson_id, competency,
                title, exam_type, difficulty, num_questions, score, total_score,
                percentage, grade, 1 if passed else 0, time_spent_minutes,
                started_at or now, completed_at or now,
                recommendations, barème,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_exam_attempts(
    student_id: int,
) -> List[Dict[str, Any]]:
    """Load all exam attempts for a student."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM exam_attempts
            WHERE student_id = ?
            ORDER BY started_at DESC
            """,
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Learning Timeline persistence helpers
# ---------------------------------------------------------------------------
def save_timeline_event(
    student_id: int,
    event_type: str,
    subject_id: Optional[str],
    lesson_id: Optional[str],
    chapter_id: Optional[str],
    title: str,
    description: Optional[str],
    score: Optional[float],
    timestamp: Optional[int],
) -> int:
    """Insert a timeline event and return its ID."""
    import time as _time
    conn = get_conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO learning_timeline
            (student_id, event_type, subject_id, lesson_id, chapter_id,
             title, description, score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_id, event_type, subject_id, lesson_id, chapter_id,
                title, description, score,
                timestamp or int(_time.time() * 1000),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_timeline_events(
    student_id: int,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Load recent timeline events for a student."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT * FROM learning_timeline
            WHERE student_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (student_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Learning Statistics persistence helpers
# ---------------------------------------------------------------------------
def save_learning_statistics(
    student_id: int,
    period_type: str,
    period_start: str,
    period_end: str,
    total_study_time_minutes: int,
    lessons_completed: int,
    quizzes_taken: int,
    exams_taken: int,
    average_quiz_score: Optional[float],
    average_exam_score: Optional[float],
    completion_rate: float,
    subject_id: Optional[str],
) -> None:
    """Upsert learning statistics for a period."""
    import time as _time
    conn = get_conn()
    try:
        now = int(_time.time() * 1000)
        row = conn.execute(
            """
            SELECT id FROM learning_statistics
            WHERE student_id = ? AND period_type = ? AND period_start = ?
              AND (subject_id IS NULL OR subject_id = ?)
            """,
            (student_id, period_type, period_start, subject_id),
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO learning_statistics
                (student_id, period_type, period_start, period_end,
                 total_study_time_minutes, lessons_completed, quizzes_taken,
                 exams_taken, average_quiz_score, average_exam_score,
                 completion_rate, subject_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id, period_type, period_start, period_end,
                    total_study_time_minutes, lessons_completed, quizzes_taken,
                    exams_taken, average_quiz_score, average_exam_score,
                    completion_rate, subject_id, now,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE learning_statistics
                SET period_end = ?, total_study_time_minutes = ?,
                    lessons_completed = ?, quizzes_taken = ?, exams_taken = ?,
                    average_quiz_score = ?, average_exam_score = ?,
                    completion_rate = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    period_end, total_study_time_minutes, lessons_completed,
                    quizzes_taken, exams_taken, average_quiz_score,
                    average_exam_score, completion_rate, now, row["id"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


def load_learning_statistics(
    student_id: int,
    period_type: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Load learning statistics for a student."""
    conn = get_conn()
    try:
        query = "SELECT * FROM learning_statistics WHERE student_id = ?"
        params: List[Any] = [student_id]
        if period_type:
            query += " AND period_type = ?"; params.append(period_type)
        if subject_id:
            query += " AND subject_id = ?"; params.append(subject_id)
        query += " ORDER BY period_start DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
