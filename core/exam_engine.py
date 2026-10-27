"""AI School OS — Phase 5.4 Exam Engine.

Handles exam generation, grading, and feedback for:
- Homework
- Quiz
- Exam
- Bac Simulation

Supports automatic grading, teacher comments, and recommendations.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from core.exam_models import ExamQuestion, ExamAttempt, ExamResult, ExamTemplate


class ExamEngine:
    """Generates, administers, and grades exams for AI School OS.

    Supports homework, quiz, exam, and bac simulation modes.
    """

    # ------------------------------------------------------------------
    # Exam Generation
    # ------------------------------------------------------------------
    def generate_exam(
        self,
        template: ExamTemplate,
        available_questions: List[dict],
    ) -> List[ExamQuestion]:
        """Generate an exam from a template and available question pool.

        Parameters
        ----------
        template:
            ExamTemplate defining what to generate.
        available_questions:
            List of question dicts from the curriculum/question bank.

        Returns
        -------
        List[ExamQuestion]
            Selected questions for the exam.
        """
        # Filter questions by subject and difficulty
        subject_questions = [
            q for q in available_questions
            if q.get("subject") == template.subject
            and q.get("difficulty", "medium") == template.difficulty
        ]

        if not subject_questions:
            # Fallback: use any questions from the subject
            subject_questions = [
                q for q in available_questions
                if q.get("subject") == template.subject
            ]

        if not subject_questions:
            return []

        # Randomly select the required number of questions
        num_questions = min(template.num_questions, len(subject_questions))
        selected = random.sample(subject_questions, num_questions)

        questions: List[ExamQuestion] = []
        for q in selected:
            questions.append(ExamQuestion(
                id=q.get("id", q.get("question_id", "")),
                question=q.get("question", ""),
                subject=q.get("subject", template.subject),
                chapter=q.get("chapter", ""),
                lesson=q.get("lesson", ""),
                competency=q.get("competency", ""),
                difficulty=q.get("difficulty", template.difficulty),
                question_type=q.get("question_type", "short_answer"),
                points=q.get("points", template.total_points // max(template.num_questions, 1)),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", ""),
                language=q.get("language", template.language),
            ))

        return questions

    def generate_homework(
        self,
        subject: str,
        chapter_id: str,
        lesson_id: str,
        competency: str,
        num_questions: int = 5,
        available_questions: Optional[List[dict]] = None,
    ) -> List[ExamQuestion]:
        """Generate homework for a specific lesson."""
        template = ExamTemplate(
            exam_id=f"hw_{subject}_{chapter_id}_{lesson_id}",
            title=f"Homework: {chapter_id} - {lesson_id}",
            subject=subject,
            chapter=chapter_id,
            lesson=lesson_id,
            competency=competency,
            exam_type="homework",
            difficulty="medium",
            num_questions=num_questions,
            time_limit_minutes=30,
            total_points=num_questions * 10,
        )
        return self.generate_exam(template, available_questions or [])

    def generate_quiz(
        self,
        subject: str,
        chapter_id: str,
        lesson_id: str,
        competency: str,
        num_questions: int = 10,
        available_questions: Optional[List[dict]] = None,
    ) -> List[ExamQuestion]:
        """Generate a quiz for a specific lesson."""
        template = ExamTemplate(
            exam_id=f"quiz_{subject}_{chapter_id}_{lesson_id}",
            title=f"Quiz: {chapter_id} - {lesson_id}",
            subject=subject,
            chapter=chapter_id,
            lesson=lesson_id,
            competency=competency,
            exam_type="quiz",
            difficulty="medium",
            num_questions=num_questions,
            time_limit_minutes=15,
            total_points=num_questions * 5,
        )
        return self.generate_exam(template, available_questions or [])

    def generate_exam_full(
        self,
        subject: str,
        chapter_id: str,
        lesson_id: str,
        competency: str,
        num_questions: int = 20,
        available_questions: Optional[List[dict]] = None,
    ) -> List[ExamQuestion]:
        """Generate a full exam for a chapter."""
        template = ExamTemplate(
            exam_id=f"exam_{subject}_{chapter_id}_{lesson_id}",
            title=f"Exam: {chapter_id} - {lesson_id}",
            subject=subject,
            chapter=chapter_id,
            lesson=lesson_id,
            competency=competency,
            exam_type="exam",
            difficulty="advanced",
            num_questions=num_questions,
            time_limit_minutes=60,
            total_points=num_questions * 10,
        )
        return self.generate_exam(template, available_questions or [])

    def generate_bac_simulation(
        self,
        subject: str,
        chapter_id: str,
        lesson_id: str,
        competency: str,
        num_questions: int = 30,
        available_questions: Optional[List[dict]] = None,
    ) -> List[ExamQuestion]:
        """Generate a BAC simulation exam."""
        template = ExamTemplate(
            exam_id=f"bac_{subject}_{chapter_id}_{lesson_id}",
            title=f"BAC Simulation: {chapter_id} - {lesson_id}",
            subject=subject,
            chapter=chapter_id,
            lesson=lesson_id,
            competency=competency,
            exam_type="bac_simulation",
            difficulty="advanced",
            num_questions=num_questions,
            time_limit_minutes=120,
            total_points=num_questions * 20,
        )
        return self.generate_exam(template, available_questions or [])

    # ------------------------------------------------------------------
    # Exam Grading
    # ------------------------------------------------------------------
    def grade_exam(
        self,
        template: ExamTemplate,
        questions: List[ExamQuestion],
        student_answers: Dict[str, str],  # question_id -> answer text
    ) -> ExamResult:
        """Grade a completed exam.

        Parameters
        ----------
        template:
            The template used to generate the exam.
        questions:
            The questions that were presented to the student.
        student_answers:
            Mapping of question_id to student's answer text.

        Returns
        -------
        ExamResult
            Complete grading result with score, percentage, grade, etc.
        """
        total_points = sum(q.points for q in questions)
        total_points_earned = 0.0
        question_results: List[ExamAttempt] = []

        for q in questions:
            student_answer = student_answers.get(q.id, "")
            is_correct = self._evaluate_answer(q, student_answer)
            points_earned = q.points if is_correct else 0.0
            total_points_earned += points_earned

            question_result = ExamAttempt(
                question_id=q.id,
                student_answer=student_answer,
                is_correct=is_correct,
                points_earned=points_earned,
                max_points=q.points,
                feedback=self._generate_feedback(q, student_answer, is_correct),
            )
            question_results.append(question_result)

        percentage = round((total_points_earned / total_points) * 100, 1) if total_points > 0 else 0.0
        grade = self._grade_from_percentage(percentage)
        passed = percentage >= template.passing_score

        feedback = self._generate_exam_feedback(percentage, grade, question_results)
        recommendations = self._generate_recommendations(question_results)

        return ExamResult(
            exam_id=template.exam_id,
            student_id="",  # Set by caller
            teacher_id="",  # Set by caller
            subject=template.subject,
            exam_type=template.exam_type,
            total_score=round(total_points_earned, 1),
            max_score=total_points,
            percentage=percentage,
            grade=grade,
            passed=passed,
            time_spent_minutes=0,  # Set by caller
            questions=question_results,
            started_at="",  # Set by caller
            completed_at=str(__import__("datetime").datetime.now()),
            feedback=feedback,
            recommendations=recommendations,
            barème=self._generate_barème(template),
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _evaluate_answer(question: ExamQuestion, student_answer: str) -> bool:
        """Evaluate if a student's answer is correct.

        Simple keyword-based matching. In production, this could use
        more sophisticated NLP.
        """
        if not student_answer or not question.correct_answer:
            return False

        student_lower = student_answer.lower().strip()
        correct_lower = question.correct_answer.lower().strip()

        # Exact match
        if student_lower == correct_lower:
            return True

        # Keyword overlap check
        student_words = set(student_lower.split())
        correct_words = set(correct_lower.split())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did", "will",
                      "would", "could", "should", "may", "might", "can", "to",
                      "of", "in", "for", "on", "with", "at", "by", "from", "as",
                      "i", "you", "he", "she", "it", "we", "they", "what", "who",
                      "where", "when", "why", "how", "?", ".", ",", "!"}

        student_keywords = student_words - stop_words
        correct_keywords = correct_words - stop_words

        if not correct_keywords:
            return False

        overlap = len(student_keywords & correct_keywords)
        return overlap >= max(1, len(correct_keywords) // 2)

    @staticmethod
    def _generate_feedback(question: ExamQuestion, answer: str, is_correct: bool) -> str:
        """Generate feedback for a single answer."""
        if is_correct:
            return f"Correct answer. Well done!"
        else:
            return f"Incorrect. Correct answer: {question.correct_answer}. {question.explanation}"

    @staticmethod
    def _generate_exam_feedback(percentage: float, grade: str, results: List[ExamAttempt]) -> str:
        """Generate overall feedback for an exam."""
        if percentage >= 90:
            return "Excellent work! You have an excellent grasp of the material."
        elif percentage >= 70:
            return "Good work! You understand most of the material. Review areas where you lost points."
        elif percentage >= 50:
            return "You have a basic understanding but need to review key concepts. Focus on weak areas."
        else:
            return "You need significant review. Please review the material thoroughly and seek help if needed."

    @staticmethod
    def _generate_recommendations(results: List[ExamAttempt]) -> List[str]:
        """Generate study recommendations based on incorrect answers."""
        recommendations = []
        incorrect = [r for r in results if not r.is_correct]

        if not incorrect:
            recommendations.append("Excellent work! You have a strong understanding of the material.")
            return recommendations

        incorrect_topics = set()
        for r in incorrect:
            # Extract topic from question_id if possible
            incorrect_topics.add(r.question_id)

        if incorrect_topics:
            recommendations.append(f"Review topics: {', '.join(sorted(incorrect_topics))}")

        recommendations.append("Review the explanations for incorrect answers.")
        recommendations.append("Practice similar problems to reinforce learning.")

        return recommendations

    @staticmethod
    def _grade_from_percentage(percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def _generate_barème(template: ExamTemplate) -> str:
        """Generate grading rubric (barème) for the exam."""
        lines = [
            f"Barème: {template.title}",
            f"Total points: {template.total_points}",
            f"Number of questions: {template.num_questions}",
            f"Points per question: {template.total_points // max(template.num_questions, 1)}",
            f"Passing score: {template.passing_score}%",
            "",
            "Grading scale:",
            "  A: 90-100%",
            "  B: 80-89%",
            "  C: 70-79%",
            "  D: 60-69%",
            "  F: Below 60%",
        ]
        return "\n".join(lines)