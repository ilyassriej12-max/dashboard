"""AI School OS — Phase 4.1 memory interface.

Provides a clean abstraction over the student's learning memory,
backed by SQLite through the existing :mod:`services.db.database`
layer.  No embeddings, no vector databases — purely relational.

Responsibilities:

* Conversation history
* Mistakes
* Weak topics
* Strong topics
* Progress
* Current curriculum
* Current teacher
* Current mission
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from services.db.database import get_conn


class Memory:
    """Student memory backed by SQLite.

    All methods operate on a single *student_id*.  The database
    connection is opened and closed per call to keep the interface
    simple and thread-safe enough for the FastAPI request cycle.
    """

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------
    def add_message(
        self,
        student_id: int,
        teacher_id: str,
        role: str,
        message: str,
    ) -> None:
        """Append a message to the conversation history.

        Parameters
        ----------
        student_id:
            The student owning this message.
        teacher_id:
            The teacher involved in the exchange.
        role:
            ``"user"`` or ``"assistant"``.
        message:
            The message text.
        """
        conn = get_conn()
        try:
            conn.execute(
                """
                INSERT INTO conversation_history
                (student_id, teacher_id, role, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, teacher_id, role, message, int(time.time() * 1000)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_history(
        self,
        student_id: int,
        teacher_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return the most recent conversation messages for a student.

        Parameters
        ----------
        student_id:
            The student whose history to retrieve.
        teacher_id:
            Optional filter to a specific teacher.
        limit:
            Maximum number of messages to return.

        Returns
        -------
        list of dict
            Each dict has ``id``, ``role``, ``message``, ``timestamp``.
        """
        conn = get_conn()
        try:
            if teacher_id:
                rows = conn.execute(
                    """
                    SELECT id, role, message, timestamp
                    FROM conversation_history
                    WHERE student_id = ? AND teacher_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (student_id, teacher_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, role, message, timestamp
                    FROM conversation_history
                    WHERE student_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (student_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Mistakes
    # ------------------------------------------------------------------
    def record_mistake(
        self,
        student_id: int,
        topic: str,
        subject_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Record that a student made a mistake on *topic*."""
        conn = get_conn()
        try:
            conn.execute(
                """
                INSERT INTO mistakes
                (student_id, subject_id, topic, description, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    subject_id,
                    topic,
                    description,
                    int(time.time() * 1000),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_mistakes(
        self,
        student_id: int,
        subject_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return recorded mistakes for a student."""
        conn = get_conn()
        try:
            if subject_id:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, description, timestamp
                    FROM mistakes
                    WHERE student_id = ? AND subject_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (student_id, subject_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, description, timestamp
                    FROM mistakes
                    WHERE student_id = ?
                    ORDER BY timestamp DESC
                    """,
                    (student_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Weak / strong topics
    # ------------------------------------------------------------------
    def set_weak_topic(
        self,
        student_id: int,
        topic: str,
        subject_id: Optional[str] = None,
        score: float = 0.0,
    ) -> None:
        """Record or update a weak topic for a student."""
        conn = get_conn()
        try:
            row = conn.execute(
                """
                SELECT id FROM weak_topics
                WHERE student_id = ? AND topic = ?
                """,
                (student_id, topic),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO weak_topics
                    (student_id, subject_id, topic, weakness_score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, subject_id, topic, score),
                )
            else:
                conn.execute(
                    """
                    UPDATE weak_topics
                    SET weakness_score = ?
                    WHERE id = ?
                    """,
                    (score, row[0]),
                )
            conn.commit()
        finally:
            conn.close()

    def get_weak_topics(
        self,
        student_id: int,
        subject_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return weak topics for a student."""
        conn = get_conn()
        try:
            if subject_id:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, weakness_score
                    FROM weak_topics
                    WHERE student_id = ? AND subject_id = ?
                    ORDER BY weakness_score DESC
                    """,
                    (student_id, subject_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, weakness_score
                    FROM weak_topics
                    WHERE student_id = ?
                    ORDER BY weakness_score DESC
                    """,
                    (student_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def set_strong_topic(
        self,
        student_id: int,
        topic: str,
        subject_id: Optional[str] = None,
        score: float = 0.0,
    ) -> None:
        """Record or update a strong topic for a student."""
        conn = get_conn()
        try:
            row = conn.execute(
                """
                SELECT id FROM strong_topics
                WHERE student_id = ? AND topic = ?
                """,
                (student_id, topic),
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO strong_topics
                    (student_id, subject_id, topic, strength_score)
                    VALUES (?, ?, ?, ?)
                    """,
                    (student_id, subject_id, topic, score),
                )
            else:
                conn.execute(
                    """
                    UPDATE strong_topics
                    SET strength_score = ?
                    WHERE id = ?
                    """,
                    (score, row[0]),
                )
            conn.commit()
        finally:
            conn.close()

    def get_strong_topics(
        self,
        student_id: int,
        subject_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return strong topics for a student."""
        conn = get_conn()
        try:
            if subject_id:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, strength_score
                    FROM strong_topics
                    WHERE student_id = ? AND subject_id = ?
                    ORDER BY strength_score DESC
                    """,
                    (student_id, subject_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, topic, subject_id, strength_score
                    FROM strong_topics
                    WHERE student_id = ?
                    ORDER BY strength_score DESC
                    """,
                    (student_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Memory state (current curriculum / teacher / mission)
    # ------------------------------------------------------------------
    def get_state(self, student_id: int) -> Dict[str, Any]:
        """Return the memory state for a student.

        Returns an empty dict if no state has been saved yet.
        """
        conn = get_conn()
        try:
            row = conn.execute(
                """
                SELECT current_curriculum, current_teacher_id,
                       current_mission, updated_at
                FROM memory_state
                WHERE student_id = ?
                """,
                (student_id,),
            ).fetchone()
            if row is None:
                return {}
            return dict(row)
        finally:
            conn.close()

    def set_state(
        self,
        student_id: int,
        current_curriculum: Optional[str] = None,
        current_teacher_id: Optional[str] = None,
        current_mission: Optional[str] = None,
    ) -> None:
        """Save or update the memory state for a student."""
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT id FROM memory_state WHERE student_id = ?",
                (student_id,),
            ).fetchone()
            now = int(time.time() * 1000)
            if row is None:
                conn.execute(
                    """
                    INSERT INTO memory_state
                    (student_id, current_curriculum, current_teacher_id,
                     current_mission, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        student_id,
                        current_curriculum,
                        current_teacher_id,
                        current_mission,
                        now,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE memory_state
                    SET current_curriculum = COALESCE(?, current_curriculum),
                        current_teacher_id = COALESCE(?, current_teacher_id),
                        current_mission = COALESCE(?, current_mission),
                        updated_at = ?
                    WHERE student_id = ?
                    """,
                    (
                        current_curriculum,
                        current_teacher_id,
                        current_mission,
                        now,
                        student_id,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
