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

from core.difficulty_engine import DifficultyEngine
from core.learning import LearningEngine
from core.memory import Memory
from core.mission_engine import MissionEngine
from core.orchestrator import Orchestrator
from core.prompt_builder import PromptBuilder
from core.student_model import StudentModel
from core.teacher_engine import TeacherEngine
from core.teaching_strategy import StrategySelector
from core.schemas import (
    CalendarEvent,
    ChatRequest,
    ChatResponse,
    DashboardResponse,
    Homework,
    HomeworkCompleteRequest,
    MessageResponse,
    Notification,
    NotesRequest,
    Profile,
    SettingsRequest,
    SettingItem,
    Teacher,
)
from services.ai.config import DEFAULT_PROVIDER, FALLBACK_PROVIDER
from services.ai.base import AIProvider
from services.ai.gemini import GeminiProvider
from services.ai.ollama import OllamaProvider
from services.ai.router import AIRouter
from services.db.database import DATABASE_PATH, get_conn, init_db

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
)


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
