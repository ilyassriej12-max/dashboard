"""AI School OS — Phase 4.4 teacher plugin loader.

Automatically discovers teacher implementations from the
``teachers/*`` directory tree without manual imports.  Each teacher
lives in its own folder and exposes a :class:`core.teacher.Teacher`
subclass.

Future teachers work simply by creating a new folder under
``teachers/`` — no changes to this loader are required.

Each teacher plugin folder should contain:

* ``teacher.py`` — defines a :class:`BaseTeacher` subclass
* ``config.json`` — teacher metadata (name, subject, model, tools, curriculum, keywords)
* ``persona.md`` — teacher personality/teaching style text

The loader automatically discovers every teacher folder.  If a new
folder appears later (e.g. ``teachers/history/``), the system loads it
automatically with no code modification.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from core.teacher import Teacher
from core.memory import Memory
from core.prompt_builder import PromptBuilder
from core.learning import LearningEngine
from core.teacher_engine import TeacherEngine
from services.ai.router import AIRouter

# Resolve the teachers directory relative to the project root.
# This file lives at <root>/core/loader.py, so:
#   parents[0] = core, parents[1] = <root>
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEACHERS_DIR = _PROJECT_ROOT / "teachers"

# Internal registry: teacher_id -> Teacher class
_teachers: Dict[str, Type[Teacher]] = {}


def load_teachers(
    router: Optional[AIRouter] = None,
    memory: Optional[Memory] = None,
    prompt_builder: Optional[PromptBuilder] = None,
    learning_engine: Optional[LearningEngine] = None,
    teacher_engine: Optional[TeacherEngine] = None,
) -> Dict[str, Type[Teacher]]:
    """Auto-discover and load every teacher under ``teachers/*``.

    Scans each immediate subdirectory of ``teachers/`` for a Python
    module (``__init__.py`` or ``teacher.py``) that defines at least
    one concrete subclass of :class:`BaseTeacher`.  Discovered classes are
    registered in the internal registry and returned.

    Parameters
    ----------
    router:
        Optional :class:`AIRouter` instance passed to each teacher.
    memory:
        Optional :class:`Memory` instance passed to each teacher.
    prompt_builder:
        Optional :class:`PromptBuilder` instance passed to each teacher.
    learning_engine:
        Optional :class:`LearningEngine` instance passed to each teacher.
    teacher_engine:
        Optional :class:`TeacherEngine` instance passed to each teacher.

    Returns
    -------
    dict
        Mapping of ``teacher_id`` -> :class:`Teacher` subclass.
    """
    _teachers.clear()

    if not TEACHERS_DIR.is_dir():
        return _teachers

    for entry in sorted(TEACHERS_DIR.iterdir()):
        if not entry.is_dir():
            continue

        # Look for __init__.py first, then teacher.py
        module_path: Optional[Path] = None
        for candidate in (entry / "__init__.py", entry / "teacher.py"):
            if candidate.is_file():
                module_path = candidate
                break

        if module_path is None:
            continue

        module_name = f"teachers.{entry.name}.teacher_module"
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, str(module_path)
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            # Register in sys.modules so relative imports inside the
            # teacher package work if needed.
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Register every concrete Teacher subclass found.
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Teacher)
                    and attr is not Teacher
                ):
                    # Instantiate to read the teacher_id, then store
                    # the class for later instantiation by the caller.
                    try:
                        instance = attr(
                            router=router,
                            memory=memory,
                            prompt_builder=prompt_builder,
                            learning_engine=learning_engine,
                            teacher_engine=teacher_engine,
                        )
                        _teachers[instance.teacher_id] = attr
                    except Exception:
                        # If a teacher cannot be instantiated with
                        # default args, skip it — the loader must not
                        # crash the whole application.
                        continue
        except Exception:
            # A broken teacher module must not break the loader.
            continue

    return _teachers


def get_teacher(teacher_id: str) -> Optional[Type[Teacher]]:
    """Return the :class:`Teacher` class registered for *teacher_id*.

    Returns ``None`` if no teacher with that ID has been loaded.
    """
    return _teachers.get(teacher_id)


def list_teachers() -> List[str]:
    """Return the IDs of all loaded teachers."""
    return list(_teachers.keys())
