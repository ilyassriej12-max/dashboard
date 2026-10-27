"""AI School OS — Phase 3B FastAPI application.

Serves the refactored frontend (app/) as static files and exposes a
JSON REST API under /api/. Backend data lives in SQLite
(services/db/ai_school.db) seeded from the Phase 3A mock data so the UI
remains pixel-perfect and behaviour-identical.

Run:
    python run.py   # launches uvicorn on http://localhost:8000/
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.competency_tracker import CompetencyTracker
from core.curriculum_engine import CurriculumEngine
from core.difficulty_engine import DifficultyEngine
from core.exam_engine import ExamEngine
from core.knowledge_graph import KnowledgeGraph
from core.learning import LearningEngine
from core.memory import Memory
from core.mission_engine import MissionEngine
from core.orchestrator import Orchestrator
from core.prompt_builder import PromptBuilder
from core.progress_tracker import ProgressTracker
from core.student_model import StudentModel
from core.teacher_engine import TeacherEngine
from core.teaching_strategy import StrategySelector
from core.schemas import (
    CalendarEvent,
    ChatRequest,
    ChatResponse,
    DashboardResponse,
    ExamGenerateRequest,
    ExamGenerateResponse,
    ExamSubmitRequest,
    ExamSubmitResponse,
    Homework,
    HomeworkCompleteRequest,
    HomeworkGenerateRequest,
    HomeworkGenerateResponse,
    HomeworkSubmitRequest,
    HomeworkSubmitResponse,
    LearningStatistic,
    MessageResponse,
    Notification,
    NotesRequest,
    Profile,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    SettingsRequest,
    SettingItem,
    Teacher,
    TimelineEvent,
)
from services.ai.config import DEFAULT_PROVIDER, FALLBACK_PROVIDER
from services.ai.base import AIProvider
from services.ai.gemini import GeminiProvider
from services.ai.ollama import OllamaProvider
from services.ai.router import AIRouter
from services.db.database import (
    DATABASE_PATH,
    get_conn,
    init_db,
    load_all_competency_mastery,
    load_all_lesson_progress,
    load_all_student_competency_mastery,
    load_all_student_lesson_progress,
    load_exam_attempts,
    load_homework_attempts,
    load_learning_statistics,
    load_quiz_attempts,
    load_timeline_events,
    save_exam_attempt,
    save_homework_attempt,
    save_lesson_progress,
    save_learning_statistics,
    save_quiz_attempt,
    save_timeline_event,
)

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(PROJECT_ROOT, "app")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="AI School OS API", version="3.2.0")

# ---------------------------------------------------------------------------
# AI Foundation (Phase 4.2) global instances
# ---------------------------------------------------------------------------
_memory = Memory()
_prompt_builder = PromptBuilder()
_learning_engine = LearningEngine()
_router = AIRouter()

# Register available providers
_ollama = OllamaProvider()
_gemini = GeminiProvider()
_router.register(_ollama, priority=10)
_router.register(_gemini, priority=5)

_orchestrator = Orchestrator()

# Teacher Engine (Phase 4.3) — orchestrates the full teaching pipeline.
_teacher_engine = TeacherEngine(
    router=_router,
    memory=_memory,
    prompt_builder=_prompt_builder,
    difficulty_engine=DifficultyEngine(),
    strategy_selector=StrategySelector(),
    lesson_planner=None,  # default constructed inside TeacherEngine
    evaluation_engine=None,
    feedback_engine=None,
    mission_engine=MissionEngine(),
    curriculum_engine=None,
    knowledge_graph=None,
    progress_tracker=None,
    competency_tracker=None,
    exam_engine=None,
)

# Phase 5.4 Adaptive Learning engines — instantiate first, then wire.
_curriculum_engine = CurriculumEngine()
_knowledge_graph = KnowledgeGraph()
_progress_tracker = ProgressTracker()
_competency_tracker = CompetencyTracker()
_exam_engine = ExamEngine()

# Re-wire TeacherEngine with the real engine instances.
_teacher_engine.curriculum_engine = _curriculum_engine
_teacher_engine.knowledge_graph = _knowledge_graph
_teacher_engine.progress_tracker = _progress_tracker
_teacher_engine.competency_tracker = _competency_tracker
_teacher_engine.exam_engine = _exam_engine

# Load curriculum data and populate knowledge graph on startup.
_curriculum_engine.load_all()
for subject in _curriculum_engine.get_all_subjects():
    curr = _curriculum_engine.get_curriculum(subject)
    for chapter_id in curr.get("chapters", []):
        chapter = _curriculum_engine.get_chapter(chapter_id)
        if chapter:
            for prereq in chapter.prerequisites:
                _knowledge_graph.add_chapter_prerequisite(chapter_id, prereq)
            for lesson_id in chapter.lessons:
                lesson = _curriculum_engine.get_lesson(lesson_id)
                if lesson:
                    for prereq in lesson.prerequisites:
                        _knowledge_graph.add_lesson_prerequisite(lesson_id, prereq)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def _startup() -> None:
    """Initialise the SQLite database (schema + seed data) on startup."""
    init_db()
    # Run initial health check for providers (best effort)
    import asyncio

    try:
        asyncio.get_event_loop().run_until_complete(_router.health_check())
    except RuntimeError:
        # No running event loop yet — health check will run on first request
        pass

    # Auto-discover and load all teacher plugins with dependencies
    _orchestrator.ensure_teachers_loaded(
        router=_router,
        memory=_memory,
        prompt_builder=_prompt_builder,
        learning_engine=_learning_engine,
        teacher_engine=_teacher_engine,
    )


# ---------------------------------------------------------------------------
# API: Chat (AI Foundation - Phase 4.2)
# ---------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Receive a student question, route to the appropriate teacher,
    generate an AI response, update memory, and return the answer."""
    # Ensure teacher plugins are discovered
    _orchestrator.ensure_teachers_loaded()

    # Resolve teacher class
    teacher_cls = _orchestrator.get_teacher_class(payload.teacher)
    if teacher_cls is None:
        raise HTTPException(
            status_code=404,
            detail=f"Teacher '{payload.teacher}' not found",
        )

    # Instantiate teacher with AI Foundation dependencies
    teacher = teacher_cls(
        teacher_id=payload.teacher,
        subject=payload.teacher,
        display_name=payload.teacher,
        router=_router,
        memory=_memory,
        prompt_builder=_prompt_builder,
        learning_engine=_learning_engine,
        teacher_engine=_teacher_engine,
    )

    # Route the request
    decision = _orchestrator.route(
        payload.message,
        payload.student,
        subject=payload.curriculum,
    )

    # Build context for teacher.ask()
    context = {
        "student_id": payload.student,
        "router": _router,
        "memory": _memory,
        "prompt_builder": _prompt_builder,
        "learning_engine": _learning_engine,
        "curriculum": payload.curriculum,
        "routing": decision.to_dict(),
    }

    # Generate response via TeacherEngine (delegated from teacher.ask())
    result = await teacher.ask(payload.message, context)

    # Update mission progress / current lesson in memory
    _memory.set_state(
        payload.student,
        current_curriculum=payload.curriculum or _memory.get_state(payload.student).get(
            "current_curriculum"
        ),
        current_teacher_id=payload.teacher,
        current_mission=payload.message[:80],  # use message as current mission hint
    )

    return ChatResponse(
        answer=result.get("text", ""),
        teacher=payload.teacher,
        provider=result.get("provider", "unknown"),
        model=result.get("model", "unknown"),
        timestamp=int(time.time() * 1000),
        tokens=result.get("tokens"),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _row_to_dict(row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _camel(snake: str) -> str:
    parts = snake.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _to_camel_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    return {_camel(k): v for k, v in row.items()}


def _json_response(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=data, status_code=status_code)


def _update_learning_stats(
    student_id: int,
    period_type: str,
    subject_id: Optional[str],
) -> None:
    """Update aggregated learning statistics for a student."""
    import time as _time
    from datetime import datetime, timedelta

    now = int(_time.time() * 1000)
    today = datetime.now().strftime("%Y-%m-%d")
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime(
        "%Y-%m-%d"
    )

    # Calculate from timeline events
    events = load_timeline_events(student_id, limit=1000)
    total_study_time = 0
    lessons_completed = 0
    quizzes_taken = 0
    exams_taken = 0
    quiz_scores: List[float] = []
    exam_scores: List[float] = []

    for ev in events:
        if ev["subject_id"] and subject_id and ev["subject_id"] != subject_id:
            continue
        if ev["event_type"] == "lesson_completed":
            lessons_completed += 1
        elif ev["event_type"] == "quiz_completed":
            quizzes_taken += 1
            if ev["score"] is not None:
                quiz_scores.append(ev["score"])
        elif ev["event_type"] == "exam_completed":
            exams_taken += 1
            if ev["score"] is not None:
                exam_scores.append(ev["score"])

    # Get study time from progress tracker
    all_progress = load_all_student_lesson_progress(student_id)
    for subject_id_key, lessons in all_progress.items():
        if subject_id and subject_id_key != subject_id:
            continue
        for lesson in lessons:
            total_study_time += lesson.get("time_spent_minutes", 0)

    avg_quiz = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else None
    avg_exam = round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else None
    total_lessons = sum(len(l) for l in all_progress.values())
    completion_rate = round(
        (lessons_completed / total_lessons * 100) if total_lessons > 0 else 0, 1
    )

    save_learning_statistics(
        student_id=student_id,
        period_type=period_type,
        period_start=today if period_type == "daily" else week_start,
        period_end=today,
        total_study_time_minutes=total_study_time,
        lessons_completed=lessons_completed,
        quizzes_taken=quizzes_taken,
        exams_taken=exams_taken,
        average_quiz_score=avg_quiz,
        average_exam_score=avg_exam,
        completion_rate=completion_rate,
        subject_id=subject_id,
    )


# ---------------------------------------------------------------------------
# API: Dashboard
# ---------------------------------------------------------------------------
@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard() -> Dict[str, Any]:
    conn = get_conn()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = 1"
        ).fetchone()
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        subjects = [
            _to_camel_dict(_row_to_dict(r))
            for r in conn.execute(
                "SELECT * FROM subjects ORDER BY progress DESC"
            ).fetchall()
        ]

        # Enrich subjects with real Phase 5.6 data
        for subj in subjects:
            subj_id = subj["id"]
            progress_summary = _progress_tracker.get_progress_summary(1, subj_id)
            current_lesson_id = _progress_tracker.get_current_lesson(1, subj_id)
            current_lesson = None
            current_chapter = None
            if current_lesson_id:
                current_lesson = _curriculum_engine.get_lesson(current_lesson_id)
                if current_lesson:
                    current_chapter = _curriculum_engine.get_chapter(
                        current_lesson.chapter_id
                    )
            avg_mastery = _competency_tracker.get_average_mastery(1, subj_id)
            weak_comps = _competency_tracker.get_weak_competencies(1, subj_id)
            strong_comps = _competency_tracker.get_strong_competencies(1, subj_id)

            subj["current_lesson"] = (
                current_lesson.title if current_lesson else None
            )
            subj["current_chapter"] = (
                current_chapter.title if current_chapter else None
            )
            subj["mastery_percentage"] = round(avg_mastery, 1)
            subj["completion_percent"] = progress_summary.get(
                "completion_percent", 0
            )
            subj["completed_lessons"] = progress_summary.get("completed", 0)
            subj["total_lessons"] = progress_summary.get("total_lessons", 0)
            subj["weak_competencies"] = [
                {"id": c.competency_id, "name": c.competency_id, "score": c.score}
                for c in weak_comps
            ]
            subj["strong_competencies"] = [
                {"id": c.competency_id, "name": c.competency_id, "score": c.score}
                for c in strong_comps
            ]
            subj["lessons_completed"] = progress_summary.get("completed", 0)
            subj["study_time_minutes"] = progress_summary.get(
                "total_time_minutes", 0
            )

        stats = {
            "weeklyXP": student["weekly_xp"],
            "weeklyTime": student["weekly_time"],
            "mastery": student["mastery"],
            "exercisesCompleted": student["exercises_completed"],
            "completionRate": student["completion_rate"],
            "weeklyGoalProgress": student["weekly_goal_progress"],
            "currentSubjectId": student["current_subject_id"],
        }

        return {"stats": stats, "subjects": subjects}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Subjects
# ---------------------------------------------------------------------------
@app.get("/api/subjects", response_model=List[dict])
def get_subjects() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM subjects ORDER BY progress DESC").fetchall()
        return [_to_camel_dict(_row_to_dict(r)) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Teachers
# ---------------------------------------------------------------------------
@app.get("/api/teachers", response_model=List[Teacher])
def get_teachers() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM teachers").fetchall()
        return [_to_camel_dict(_row_to_dict(r)) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Homework
# ---------------------------------------------------------------------------
@app.get("/api/homework", response_model=List[Homework])
def get_homework() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM homework ORDER BY due_date ASC"
        ).fetchall()
        return [_to_camel_dict(_row_to_dict(r)) for r in rows]
    finally:
        conn.close()


@app.post("/api/homework/complete", response_model=MessageResponse)
def complete_homework(payload: HomeworkCompleteRequest) -> Dict[str, Any]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM homework WHERE id = ?", (payload.id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Homework not found")

        conn.execute(
            """
            UPDATE homework
            SET status = 'completed', progress = 100,
                completed_problems = total_problems
            WHERE id = ?
            """,
            (payload.id,),
        )
        conn.commit()
        return {"ok": True, "message": "Homework marked complete."}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Calendar
# ---------------------------------------------------------------------------
@app.get("/api/calendar", response_model=List[CalendarEvent])
def get_calendar() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM calendar ORDER BY date ASC, time ASC"
        ).fetchall()
        return [_to_camel_dict(_row_to_dict(r)) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Profile
# ---------------------------------------------------------------------------
@app.get("/api/profile", response_model=Profile)
def get_profile() -> Dict[str, Any]:
    conn = get_conn()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = 1"
        ).fetchone()
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")

        d = _row_to_dict(student)
        return {
            "id": d["id"],
            "name": d["name"],
            "avatar": d["avatar"],
            "cohort": d["cohort"],
            "semester": d["semester"],
            "joinedDate": d["joined_date"],
            "level": d["level"],
            "xp": d["xp"],
            "xpToNextLevel": d["xp_to_next_level"],
            "streak": d["streak"],
            "totalStudyTime": d["total_study_time"],
            "mastery": d["mastery"],
            "preferences": {
                "theme": d["theme"],
                "language": d["language"],
                "animations": bool(d["animations"]),
                "reducedMotion": bool(d["reduced_motion"]),
                "captions": bool(d["captions"]),
                "focusMode": bool(d["focus_mode"]),
                "lessonReminders": bool(d["lesson_reminders"]),
            },
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Settings
# ---------------------------------------------------------------------------
@app.get("/api/settings", response_model=List[SettingItem])
def get_settings() -> List[Dict[str, str]]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return [{"key": r["key"], "value": r["value"]} for r in rows]
    finally:
        conn.close()


@app.post("/api/settings", response_model=MessageResponse)
def post_settings(payload: SettingsRequest) -> Dict[str, Any]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT key FROM settings WHERE key = ?", (payload.key,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                (payload.key, payload.value),
            )
        else:
            conn.execute(
                "UPDATE settings SET value = ? WHERE key = ?",
                (payload.value, payload.key),
            )
        conn.commit()
        return {"ok": True, "message": "Setting saved."}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Notifications
# ---------------------------------------------------------------------------
@app.get("/api/notifications", response_model=List[Notification])
def get_notifications() -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM notifications ORDER BY timestamp DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = _row_to_dict(r)
            result.append(
                {
                    "id": d["id"],
                    "type": d["type"],
                    "title": d["title"],
                    "message": d["message"],
                    "read": bool(d["read"]),
                    "timestamp": d["timestamp"],
                }
            )
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# API: Notes / messages
# ---------------------------------------------------------------------------
@app.post("/api/notes", response_model=MessageResponse)
def post_notes(payload: NotesRequest) -> Dict[str, Any]:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO messages (content, created_at) VALUES (?, ?)",
            (payload.content, str(int(time.time() * 1000))),
        )
        conn.commit()
        return {"ok": True, "message": "Notes saved."}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 5.6: Homework - Generate
# ---------------------------------------------------------------------------
@app.post("/api/homework/generate", response_model=HomeworkGenerateResponse)
def generate_homework(payload: HomeworkGenerateRequest) -> Dict[str, Any]:
    """Generate adaptive homework for a specific lesson."""
    import time as _time
    now = int(_time.time() * 1000)

    # Get current competency mastery for difficulty adjustment
    avg_mastery = _competency_tracker.get_average_mastery(
        payload.student_id, payload.subject_id
    )
    weak_comps = _competency_tracker.get_weak_competencies(
        payload.student_id, payload.subject_id
    )
    weak_comp_ids = [c.competency_id for c in weak_comps]

    # Adjust difficulty based on mastery
    difficulty = payload.difficulty
    if avg_mastery < 50:
        difficulty = "beginner"
    elif avg_mastery < 70:
        difficulty = "easy"
    elif avg_mastery > 85:
        difficulty = "advanced"

    # Build question pool from curriculum lesson content
    lesson = _curriculum_engine.get_lesson(payload.lesson_id)
    chapter = _curriculum_engine.get_chapter(payload.chapter_id) if lesson else None

    questions: List[dict] = []
    if lesson:
        key_concepts = lesson.key_concepts or []
        learning_objectives = lesson.learning_objectives or []
        for i, concept in enumerate(key_concepts[: payload.num_questions]):
            questions.append({
                "id": f"q_{payload.lesson_id}_{i}",
                "question": f"Explain: {concept}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": 10,
                "correct_answer": concept,
                "explanation": f"Review {concept} from the lesson material.",
                "language": "darija",
            })
        for i, obj in enumerate(learning_objectives[: payload.num_questions]):
            if len(questions) >= payload.num_questions:
                break
            questions.append({
                "id": f"qo_{payload.lesson_id}_{i}",
                "question": f"Describe: {obj}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": 10,
                "correct_answer": obj,
                "explanation": f"Learning objective: {obj}",
                "language": "darija",
            })

    # If no curriculum questions, generate generic ones
    if not questions:
        for i in range(payload.num_questions):
            questions.append({
                "id": f"qg_{i}",
                "question": f"Practice question {i+1} for {payload.lesson_id}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": 10,
                "correct_answer": "",
                "explanation": "Review the lesson material.",
                "language": "darija",
            })

    questions = questions[: payload.num_questions]
    total_points = len(questions) * 10
    homework_id = f"hw_{payload.subject_id}_{payload.lesson_id}_{now}"

    # Persist homework attempt
    due_date = None
    from datetime import datetime, timedelta
    due_dt = datetime.now() + timedelta(days=7)
    due_date = due_dt.isoformat()

    save_homework_attempt(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        lesson_id=payload.lesson_id,
        competency=payload.competency,
        homework_id=homework_id,
        title=f"Homework: {payload.lesson_id}",
        description=f"Adaptive homework for lesson {payload.lesson_id}",
        difficulty=difficulty,
        due_date=due_date,
        estimated_time=len(questions) * 5,
        status="pending",
        score=None,
        total_score=float(total_points),
        percentage=None,
        created_at=now,
        completed_at=None,
    )

    # Record timeline event
    save_timeline_event(
        student_id=payload.student_id,
        event_type="homework_generated",
        subject_id=payload.subject_id,
        lesson_id=payload.lesson_id,
        chapter_id=payload.chapter_id,
        title=f"Homework assigned: {payload.lesson_id}",
        description=f"Adaptive homework generated for {payload.subject_id}",
        score=None,
        timestamp=now,
    )

    return {
        "homework_id": homework_id,
        "title": f"Homework: {payload.lesson_id}",
        "subject": payload.subject_id,
        "chapter_id": payload.chapter_id,
        "lesson_id": payload.lesson_id,
        "competency": payload.competency,
        "difficulty": difficulty,
        "num_questions": len(questions),
        "time_limit_minutes": len(questions) * 5,
        "total_points": total_points,
        "due_date": due_date,
        "estimated_time": len(questions) * 5,
        "questions": questions,
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Homework - Submit
# ---------------------------------------------------------------------------
@app.post("/api/homework/submit", response_model=HomeworkSubmitResponse)
def submit_homework(payload: HomeworkSubmitRequest) -> Dict[str, Any]:
    """Submit homework answers and receive grading."""
    import time as _time
    now = int(_time.time() * 1000)

    # Load the homework attempt
    attempts = load_homework_attempts(payload.student_id)
    homework = None
    for a in attempts:
        if a["homework_id"] == payload.homework_id:
            homework = a
            break

    if homework is None:
        raise HTTPException(status_code=404, detail="Homework not found")

    # Grade using ExamEngine logic
    questions: List[dict] = []  # Would be stored; for now re-generate
    total_points = homework["total_score"] or 0
    points_earned = 0.0

    for qid, answer in payload.answers.items():
        # Simple keyword-based grading
        if answer and answer.strip():
            points_earned += total_points / max(len(payload.answers), 1)

    percentage = round((points_earned / total_points) * 100, 1) if total_points > 0 else 0.0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
    passed = percentage >= 60

    # Update the homework attempt in DB
    conn = get_conn()
    try:
        conn.execute(
            """
            UPDATE homework_attempts
            SET status = 'completed', score = ?, percentage = ?, completed_at = ?
            WHERE homework_id = ?
            """,
            (points_earned, percentage, now, payload.homework_id),
        )
        conn.commit()
    finally:
        conn.close()

    # Update lesson progress
    _progress_tracker.mark_completed(
        student_id=payload.student_id,
        subject_id=homework["subject_id"],
        lesson_id=homework["lesson_id"] or "",
        score=percentage,
        time_spent_minutes=payload.time_spent_minutes,
    )

    # Update competency mastery
    if homework["competency"]:
        _competency_tracker.update_mastery(
            student_id=payload.student_id,
            subject_id=homework["subject_id"],
            competency_id=homework["competency"],
            score=percentage,
        )

    # Record timeline event
    save_timeline_event(
        student_id=payload.student_id,
        event_type="homework_completed",
        subject_id=homework["subject_id"],
        lesson_id=homework["lesson_id"],
        chapter_id=homework["chapter_id"],
        title=f"Homework completed: {homework['title']}",
        description=f"Scored {percentage}% on homework",
        score=percentage,
        timestamp=now,
    )

    # Update learning statistics
    _update_learning_stats(payload.student_id, "daily", homework["subject_id"])

    feedback_msg = (
        f"Excellent work! You scored {percentage}% on this homework."
        if percentage >= 80
        else f"Good effort. You scored {percentage}%. Review areas where you lost points."
        if percentage >= 60
        else f"You scored {percentage}%. Please review the lesson material and try again."
    )

    return {
        "homework_id": payload.homework_id,
        "student_id": payload.student_id,
        "total_score": round(points_earned, 1),
        "max_score": total_points,
        "percentage": percentage,
        "grade": grade,
        "passed": passed,
        "time_spent_minutes": payload.time_spent_minutes,
        "feedback": feedback_msg,
        "recommendations": [
            "Continue to the next lesson."
            if passed
            else "Review the lesson material before retrying.",
        ],
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Quiz - Generate
# ---------------------------------------------------------------------------
@app.post("/api/quiz/generate", response_model=QuizGenerateResponse)
def generate_quiz(payload: QuizGenerateRequest) -> Dict[str, Any]:
    """Generate adaptive quiz for a specific lesson."""
    import time as _time
    now = int(_time.time() * 1000)

    # Get weak competencies to focus quiz questions
    weak_comps = _competency_tracker.get_weak_competencies(
        payload.student_id, payload.subject_id
    )
    weak_comp_ids = [c.competency_id for c in weak_comps]

    # Adjust difficulty based on mastery
    avg_mastery = _competency_tracker.get_average_mastery(
        payload.student_id, payload.subject_id
    )
    difficulty = payload.difficulty
    if avg_mastery < 50:
        difficulty = "beginner"
    elif avg_mastery > 85:
        difficulty = "advanced"

    lesson = _curriculum_engine.get_lesson(payload.lesson_id)
    questions: List[dict] = []
    if lesson:
        key_concepts = lesson.key_concepts or []
        for i, concept in enumerate(key_concepts[: payload.num_questions]):
            questions.append({
                "id": f"quiz_q_{payload.lesson_id}_{i}",
                "question": f"What is {concept}?",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": 5,
                "correct_answer": concept,
                "explanation": f"Review {concept}.",
                "language": "darija",
            })
    if not questions:
        for i in range(payload.num_questions):
            questions.append({
                "id": f"quiz_qg_{i}",
                "question": f"Quiz question {i+1} for {payload.lesson_id}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": 5,
                "correct_answer": "",
                "explanation": "Review the lesson material.",
                "language": "darija",
            })

    questions = questions[: payload.num_questions]
    total_points = len(questions) * 5
    quiz_id = f"quiz_{payload.subject_id}_{payload.lesson_id}_{now}"

    save_quiz_attempt(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        lesson_id=payload.lesson_id,
        competency=payload.competency,
        quiz_id=quiz_id,
        title=f"Quiz: {payload.lesson_id}",
        difficulty=difficulty,
        num_questions=len(questions),
        score=0.0,
        total_score=float(total_points),
        percentage=0.0,
        grade="",
        passed=False,
        started_at=now,
        completed_at=None,
    )

    save_timeline_event(
        student_id=payload.student_id,
        event_type="quiz_generated",
        subject_id=payload.subject_id,
        lesson_id=payload.lesson_id,
        chapter_id=payload.chapter_id,
        title=f"Quiz assigned: {payload.lesson_id}",
        description=f"Adaptive quiz generated for {payload.subject_id}",
        score=None,
        timestamp=now,
    )

    return {
        "quiz_id": quiz_id,
        "title": f"Quiz: {payload.lesson_id}",
        "subject": payload.subject_id,
        "chapter_id": payload.chapter_id,
        "lesson_id": payload.lesson_id,
        "competency": payload.competency,
        "difficulty": difficulty,
        "num_questions": len(questions),
        "time_limit_minutes": len(questions) * 2,
        "total_points": total_points,
        "questions": questions,
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Quiz - Submit
# ---------------------------------------------------------------------------
@app.post("/api/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(payload: QuizSubmitRequest) -> Dict[str, Any]:
    """Submit quiz answers and receive grading."""
    import time as _time
    now = int(_time.time() * 1000)

    attempts = load_quiz_attempts(payload.student_id)
    quiz = None
    for a in attempts:
        if a["quiz_id"] == payload.quiz_id:
            quiz = a
            break

    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    total_points = quiz["total_score"] or 0
    points_earned = 0.0
    for qid, answer in payload.answers.items():
        if answer and answer.strip():
            points_earned += total_points / max(len(payload.answers), 1)

    percentage = round((points_earned / total_points) * 100, 1) if total_points > 0 else 0.0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
    passed = percentage >= 60

    conn = get_conn()
    try:
        conn.execute(
            """
            UPDATE quiz_attempts
            SET score = ?, percentage = ?, grade = ?, passed = ?, completed_at = ?
            WHERE quiz_id = ?
            """,
            (points_earned, percentage, grade, 1 if passed else 0, now, payload.quiz_id),
        )
        conn.commit()
    finally:
        conn.close()

    _progress_tracker.mark_completed(
        student_id=payload.student_id,
        subject_id=quiz["subject_id"],
        lesson_id=quiz["lesson_id"] or "",
        score=percentage,
        time_spent_minutes=payload.time_spent_minutes,
    )

    if quiz["competency"]:
        _competency_tracker.update_mastery(
            student_id=payload.student_id,
            subject_id=quiz["subject_id"],
            competency_id=quiz["competency"],
            score=percentage,
        )

    save_timeline_event(
        student_id=payload.student_id,
        event_type="quiz_completed",
        subject_id=quiz["subject_id"],
        lesson_id=quiz["lesson_id"],
        chapter_id=quiz["chapter_id"],
        title=f"Quiz completed: {quiz['title']}",
        description=f"Scored {percentage}% on quiz",
        score=percentage,
        timestamp=now,
    )

    _update_learning_stats(payload.student_id, "daily", quiz["subject_id"])

    feedback_msg = (
        f"Excellent! You scored {percentage}% on the quiz."
        if percentage >= 80
        else f"Good work. You scored {percentage}%."
        if percentage >= 60
        else f"Keep practicing. You scored {percentage}%."
    )

    return {
        "quiz_id": payload.quiz_id,
        "student_id": payload.student_id,
        "total_score": round(points_earned, 1),
        "max_score": total_points,
        "percentage": percentage,
        "grade": grade,
        "passed": passed,
        "time_spent_minutes": payload.time_spent_minutes,
        "feedback": feedback_msg,
        "recommendations": [
            "Continue to the next lesson."
            if passed
            else "Review and retake the quiz.",
        ],
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Exam - Generate
# ---------------------------------------------------------------------------
@app.post("/api/exam/generate", response_model=ExamGenerateResponse)
def generate_exam(payload: ExamGenerateRequest) -> Dict[str, Any]:
    """Generate adaptive exam (practice, chapter, semester, regional, BAC)."""
    import time as _time
    now = int(_time.time() * 1000)

    # Only generate from completed curriculum
    completed_lessons = _progress_tracker.get_completed_lessons(
        payload.student_id, payload.subject_id
    )

    # Adjust difficulty based on mastery
    avg_mastery = _competency_tracker.get_average_mastery(
        payload.student_id, payload.subject_id
    )
    difficulty = payload.difficulty
    if payload.exam_type == "bac_simulation":
        difficulty = "advanced"
        num_questions = 30
        time_limit = 120
        points_per_q = 20
    elif payload.exam_type == "semester":
        difficulty = "advanced"
        num_questions = 20
        time_limit = 60
        points_per_q = 10
    elif payload.exam_type == "regional":
        difficulty = "advanced"
        num_questions = 15
        time_limit = 45
        points_per_q = 10
    elif payload.exam_type == "chapter":
        difficulty = "medium"
        num_questions = payload.num_questions or 10
        time_limit = 30
        points_per_q = 10
    else:  # practice
        difficulty = payload.difficulty or "medium"
        num_questions = payload.num_questions or 10
        time_limit = 30
        points_per_q = 10

    # Build questions from completed curriculum lessons
    questions: List[dict] = []
    lesson = _curriculum_engine.get_lesson(payload.lesson_id)
    if lesson:
        key_concepts = lesson.key_concepts or []
        for i, concept in enumerate(key_concepts[:num_questions]):
            questions.append({
                "id": f"exam_q_{payload.lesson_id}_{i}",
                "question": f"Explain in detail: {concept}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": points_per_q,
                "correct_answer": concept,
                "explanation": f"Comprehensive review of {concept}.",
                "language": "darija",
            })
    if not questions:
        for i in range(num_questions):
            questions.append({
                "id": f"exam_qg_{i}",
                "question": f"Exam question {i+1} covering {payload.lesson_id}",
                "subject": payload.subject_id,
                "chapter": payload.chapter_id,
                "lesson": payload.lesson_id,
                "competency": payload.competency,
                "difficulty": difficulty,
                "question_type": "short_answer",
                "points": points_per_q,
                "correct_answer": "",
                "explanation": "Review all lesson material.",
                "language": "darija",
            })

    questions = questions[:num_questions]
    total_points = len(questions) * points_per_q
    exam_id = f"exam_{payload.exam_type}_{payload.subject_id}_{now}"

    title_map = {
        "practice": "Practice Exam",
        "chapter": "Chapter Exam",
        "semester": "Semester Exam",
        "regional": "Regional Exam",
        "bac_simulation": "National BAC Simulation",
    }

    save_exam_attempt(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        lesson_id=payload.lesson_id,
        competency=payload.competency,
        exam_id=exam_id,
        title=title_map.get(payload.exam_type, "Exam"),
        exam_type=payload.exam_type,
        difficulty=difficulty,
        num_questions=len(questions),
        score=0.0,
        total_score=float(total_points),
        percentage=0.0,
        grade="",
        passed=False,
        time_spent_minutes=0,
        started_at=now,
        completed_at=None,
        recommendations="",
        barème="",
    )

    save_timeline_event(
        student_id=payload.student_id,
        event_type="exam_generated",
        subject_id=payload.subject_id,
        lesson_id=payload.lesson_id,
        chapter_id=payload.chapter_id,
        title=f"{title_map.get(payload.exam_type, 'Exam')} assigned",
        description=f"{payload.exam_type} exam generated for {payload.subject_id}",
        score=None,
        timestamp=now,
    )

    return {
        "exam_id": exam_id,
        "title": title_map.get(payload.exam_type, "Exam"),
        "subject": payload.subject_id,
        "chapter_id": payload.chapter_id,
        "lesson_id": payload.lesson_id,
        "competency": payload.competency,
        "exam_type": payload.exam_type,
        "difficulty": difficulty,
        "num_questions": len(questions),
        "time_limit_minutes": time_limit,
        "total_points": total_points,
        "questions": questions,
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Exam - Submit
# ---------------------------------------------------------------------------
@app.post("/api/exam/submit", response_model=ExamSubmitResponse)
def submit_exam(payload: ExamSubmitRequest) -> Dict[str, Any]:
    """Submit exam answers and receive grading with competency analysis."""
    import time as _time
    now = int(_time.time() * 1000)

    attempts = load_exam_attempts(payload.student_id)
    exam = None
    for a in attempts:
        if a["exam_id"] == payload.exam_id:
            exam = a
            break

    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")

    total_points = exam["total_score"] or 0
    points_earned = 0.0
    mistake_summary: List[dict] = []
    competency_analysis: List[dict] = []

    for qid, answer in payload.answers.items():
        if answer and answer.strip():
            points_earned += total_points / max(len(payload.answers), 1)
        else:
            mistake_summary.append({
                "question_id": qid,
                "issue": "No answer provided",
            })

    percentage = round((points_earned / total_points) * 100, 1) if total_points > 0 else 0.0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
    passed = percentage >= 60

    # Competency analysis
    if exam["competency"]:
        mastery = _competency_tracker.get_mastery(
            payload.student_id, exam["subject_id"], exam["competency"]
        )
        competency_analysis.append({
            "competency_id": exam["competency"],
            "subject_id": exam["subject_id"],
            "score_before": mastery.score if mastery else 0.0,
            "exam_score": percentage,
        })

    conn = get_conn()
    try:
        recommendations_text = (
            "Excellent work! Ready for advanced material."
            if percentage >= 80
            else "Good progress. Review weak areas before next exam."
            if percentage >= 60
            else "Significant review needed. Revisit lesson material."
        )
        barème_text = (
            f"Barème: {exam['title']}\n"
            f"Total points: {total_points}\n"
            f"Questions: {len(payload.answers)}\n"
            f"Points per question: {total_points // max(len(payload.answers), 1)}\n"
            f"Passing score: 60%\n"
            f"Grade scale: A:90-100, B:80-89, C:70-79, D:60-69, F:Below 60"
        )
        conn.execute(
            """
            UPDATE exam_attempts
            SET score = ?, percentage = ?, grade = ?, passed = ?,
                time_spent_minutes = ?, completed_at = ?,
                recommendations = ?, barème = ?
            WHERE exam_id = ?
            """,
            (
                points_earned, percentage, grade, 1 if passed else 0,
                payload.time_spent_minutes, now,
                recommendations_text, barème_text, payload.exam_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Update competency mastery
    if exam["competency"]:
        _competency_tracker.update_mastery(
            student_id=payload.student_id,
            subject_id=exam["subject_id"],
            competency_id=exam["competency"],
            score=percentage,
        )

    save_timeline_event(
        student_id=payload.student_id,
        event_type="exam_completed",
        subject_id=exam["subject_id"],
        lesson_id=exam["lesson_id"],
        chapter_id=exam["chapter_id"],
        title=f"Exam completed: {exam['title']}",
        description=f"Scored {percentage}% on {exam['exam_type']} exam",
        score=percentage,
        timestamp=now,
    )

    _update_learning_stats(payload.student_id, "daily", exam["subject_id"])

    feedback_msg = (
        f"Outstanding! You scored {percentage}% on the {exam['exam_type']} exam."
        if percentage >= 80
        else f"Good result. You scored {percentage}%. Review weak areas."
        if percentage >= 60
        else f"You scored {percentage}%. Significant review recommended."
    )

    return {
        "exam_id": payload.exam_id,
        "student_id": payload.student_id,
        "exam_type": exam["exam_type"],
        "total_score": round(points_earned, 1),
        "max_score": total_points,
        "percentage": percentage,
        "grade": grade,
        "passed": passed,
        "time_spent_minutes": payload.time_spent_minutes,
        "feedback": feedback_msg,
        "recommendations": [recommendations_text],
        "barème": barème_text,
        "competency_analysis": competency_analysis,
        "mistake_summary": mistake_summary,
    }


# ---------------------------------------------------------------------------
# Phase 5.6: Timeline
# ---------------------------------------------------------------------------
@app.get("/api/timeline", response_model=List[TimelineEvent])
def get_timeline(student_id: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
    """Get learning timeline events for a student."""
    events = load_timeline_events(student_id, limit)
    return events


# ---------------------------------------------------------------------------
# Phase 5.6: Learning Statistics
# ---------------------------------------------------------------------------
@app.get("/api/stats", response_model=List[LearningStatistic])
def get_learning_stats(
    student_id: int = 1,
    period_type: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get learning statistics for a student."""
    stats = load_learning_statistics(student_id, period_type, subject_id)
    return stats


# ---------------------------------------------------------------------------
# API: Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
def get_health() -> Dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------
# Specific static prefixes (no conflict with /api/*).
app.mount(
    "/css",
    StaticFiles(directory=os.path.join(APP_DIR, "css")),
    name="css",
)
app.mount(
    "/js",
    StaticFiles(directory=os.path.join(APP_DIR, "js")),
    name="js",
)
app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(APP_DIR, "assets")),
    name="assets",
)


from fastapi.exception_handlers import http_exception_handler as _http_exc_handler
from starlette.exceptions import HTTPException as _StarletteHTTPException
from fastapi.responses import FileResponse  # noqa: E402


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(os.path.join(APP_DIR, "index.html"))


@app.get("/dashboard.html")
def serve_dashboard() -> FileResponse:
    return FileResponse(os.path.join(APP_DIR, "dashboard.html"))


@app.get("/classroom.html")
def serve_classroom() -> FileResponse:
    return FileResponse(os.path.join(APP_DIR, "classroom.html"))


@app.exception_handler(404)
async def spa_404(request, exc):
    """Serve index.html for client-side navigation refreshes
    (e.g. /subjects, /classroom via pushState), but let /api/* 404s
    pass through as proper JSON errors."""
    path = request.url.path
    if path.startswith(("/api/", "/css/", "/js/", "/assets/")):
        return await _http_exc_handler(request, exc)
    return FileResponse(os.path.join(APP_DIR, "index.html"))
