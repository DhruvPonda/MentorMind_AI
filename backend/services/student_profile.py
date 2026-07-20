from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from backend.database import get_db


def get_student_profile(student_id: str) -> Optional[Dict]:
    """Get complete student profile including all mastery scores."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get student info
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()

        if not student:
            return None

        # Get mastery scores
        cursor.execute(
            "SELECT topic, score, question_count, correct_count, last_updated "
            "FROM mastery_scores WHERE student_id = ? ORDER BY score DESC",
            (student_id,)
        )
        mastery_rows = cursor.fetchall()

    mastery_scores = {}
    for row in mastery_rows:
        mastery_scores[row["topic"]] = {
            "score": row["score"],
            "question_count": row["question_count"],
            "correct_count": row["correct_count"],
            "last_updated": row["last_updated"]
        }

    strengths, weaknesses = get_strengths_and_weaknesses(student_id)

    return {
        "student_id": student["id"],
        "name": student["name"],
        "email": student["email"],
        "created_at": student["created_at"],
        "last_active": student["last_active"],
        "mastery_scores": mastery_scores,
        "strengths": strengths,
        "weaknesses": weaknesses
    }


def update_mastery(
    student_id: str,
    topic: str,
    understanding_score: float,
    confidence: float = 0.5
) -> None:
    """
    Update mastery score using exponential moving average.
    
    Args:
        student_id: The student's UUID
        topic: The topic being assessed
        understanding_score: 0.0-1.0 from the assessment agent
        confidence: 0.0-1.0, controls the weight of this update
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Get existing mastery
        cursor.execute(
            "SELECT score, question_count, correct_count FROM mastery_scores "
            "WHERE student_id = ? AND topic = ?",
            (student_id, topic)
        )
        existing = cursor.fetchone()

        now = datetime.now(timezone.utc).isoformat()

        if existing:
            # Exponential moving average: new_score = alpha * new + (1 - alpha) * old
            alpha = min(0.4, confidence * 0.5)  # Weight based on assessment confidence
            new_score = alpha * understanding_score + (1 - alpha) * existing["score"]
            new_score = max(0.0, min(1.0, new_score))

            question_count = existing["question_count"] + 1
            correct_count = existing["correct_count"] + (
                1 if understanding_score >= 0.6 else 0
            )

            cursor.execute(
                "UPDATE mastery_scores SET score = ?, question_count = ?, "
                "correct_count = ?, last_updated = ? "
                "WHERE student_id = ? AND topic = ?",
                (new_score, question_count, correct_count, now, student_id, topic)
            )
        else:
            # First time seeing this topic
            cursor.execute(
                "INSERT INTO mastery_scores "
                "(student_id, topic, score, question_count, correct_count, last_updated) "
                "VALUES (?, ?, ?, 1, ?, ?)",
                (
                    student_id, topic, understanding_score,
                    1 if understanding_score >= 0.6 else 0,
                    now
                )
            )

        # Update last_active timestamp on the student
        cursor.execute(
            "UPDATE students SET last_active = ? WHERE id = ?",
            (now, student_id)
        )


def get_strengths_and_weaknesses(
    student_id: str,
) -> Tuple[List[str], List[str]]:
    """
    Categorize topics into strengths (score >= 0.7) and weaknesses (score < 0.4).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT topic, score FROM mastery_scores WHERE student_id = ?",
            (student_id,)
        )
        rows = cursor.fetchall()

    strengths = [row["topic"] for row in rows if row["score"] >= 0.7]
    weaknesses = [row["topic"] for row in rows if row["score"] < 0.4]

    return strengths, weaknesses


def get_mastery_for_topic(student_id: str, topic: str) -> float:
    """Get the mastery score for a specific topic. Returns 0.0 if no data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT score FROM mastery_scores WHERE student_id = ? AND topic = ?",
            (student_id, topic)
        )
        row = cursor.fetchone()
    return row["score"] if row else 0.0
