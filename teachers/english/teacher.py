"""English teacher plugin.

Inherits from BaseTeacher. Contains no business logic — all teaching
intelligence lives in TeacherEngine. This plugin only provides
teacher metadata loaded from config.json and persona.md via
BaseTeacher.from_plugin_dir().
"""

from __future__ import annotations

from pathlib import Path
import json

from core.teacher_engine import TeacherEngine
from teachers.base_teacher import BaseTeacher
from services.ai.router import AIRouter
from core.memory import Memory
from core.prompt_builder import PromptBuilder
from core.learning import LearningEngine


class EnglishTeacher(BaseTeacher):
    """English teacher plugin."""

    def __init__(
        self,
        router: AIRouter | None = None,
        memory: Memory | None = None,
        prompt_builder: PromptBuilder | None = None,
        learning_engine: LearningEngine | None = None,
        teacher_engine: TeacherEngine | None = None,
        teacher_id: str | None = None,
        subject: str | None = None,
        display_name: str | None = None,
    ) -> None:
        plugin_dir = Path(__file__).resolve().parent
        config_path = plugin_dir / "config.json"
        persona_path = plugin_dir / "persona.md"

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        with open(persona_path, "r", encoding="utf-8") as f:
            persona = f.read()

        super().__init__(
            teacher_id=teacher_id or config.get("name", "english").lower().replace(" ", "_"),
            subject=subject or config.get("subject", "English"),
            display_name=display_name or config.get("name", "English"),
            description=config.get("description", ""),
            supported_curriculum=config.get("curriculum", []),
            supported_tools=config.get("allowed_tools", []),
            model_preference=config.get("model"),
            explanation_style=config.get("explanation_style", "concept-first"),
            reasoning_style=config.get("reasoning_style", "inductive"),
            vocabulary=config.get("vocabulary", []),
            examples=config.get("examples", []),
            preferred_lesson_flow=config.get("preferred_lesson_flow", []),
            correction_style=config.get("correction_style", "gentle"),
            teaching_personality=config.get("teaching_personality", "inspiring"),
            objectives=config.get("objectives", []),
            restrictions=config.get("restrictions", []),
            keywords=config.get("keywords", []),
            difficulty_preference=config.get("difficulty_preference", "beginner"),
            router=router,
            memory=memory,
            prompt_builder=prompt_builder,
            learning_engine=learning_engine,
            teacher_engine=teacher_engine,
            persona=persona,
            config=config,
        )
