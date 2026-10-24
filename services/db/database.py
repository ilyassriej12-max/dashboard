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

        # Seed only when tables are empty (idempotent).
        if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            _seed(conn)
        conn.commit()
    finally:
        conn.close()


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
