"""Assessment Agent: evaluates student understanding and generates quizzes."""

import os
import json
from typing import Dict, List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.services.student_profile import update_mastery, get_mastery_for_topic
from backend.services.topic_detector import detect_topic

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1,
    max_tokens=500,
    api_key=os.getenv("GROQ_API_KEY"),
)

ASSESSMENT_PROMPT = """You are an educational assessment agent for MentorMind AI.
Analyze the conversation and return a JSON evaluation:
{
    "understanding_score": <float 0.0-1.0, where 0=no understanding, 1=complete mastery>,
    "confidence": <float 0.0-1.0, how confident you are in your assessment>,
    "misconceptions": [<list of identified misconceptions, empty if none>],
    "recommendation": "<brief suggestion for next steps>"
}

Assessment criteria:
- Basic "what is" question: 0.3-0.5
- Follow-up showing deeper curiosity: 0.5-0.7
- Demonstrated application of the concept: 0.7-0.9
- Corrected a previous misconception: boost score
- Showed confusion or asked for re-explanation: 0.2-0.4
- Consider the student's previous mastery score as context

IMPORTANT: Respond with ONLY valid JSON, no other text."""

QUIZ_PROMPT = """You are a quiz generation agent for MentorMind AI.
Generate exactly 3 quiz questions about the given topic, appropriate for the student's mastery level.

Return ONLY a JSON array:
[
    {
        "question": "The quiz question text",
        "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
        "correct_answer": "A) option1"
    }
]

Difficulty based on mastery:
- Low mastery (< 0.4): Beginner conceptual questions
- Medium mastery (0.4-0.7): Application-level questions
- High mastery (> 0.7): Advanced/analytical questions

IMPORTANT: Respond with ONLY valid JSON array, no other text."""


def _parse_json(text: str):
    """Parse JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def assessment_node(state: dict) -> dict:
    """Evaluate understanding (chat mode) or generate quizzes (quiz mode)."""
    route = state.get("route", "chat")
    student_id = state.get("student_id", "")
    profile = state.get("student_profile")

    if route == "quiz":
        return _handle_quiz(state, student_id, profile)
    else:
        return _handle_assessment(state, student_id, profile)


def _handle_assessment(
    state: dict, student_id: str, profile: Optional[Dict]
) -> dict:
    """Evaluate student understanding from the tutor conversation."""
    question = state.get("question", "")
    tutor_response = state.get("tutor_response", "")
    topic = state.get("topic", "general")
    previous_mastery = get_mastery_for_topic(student_id, topic)

    context = (
        f"Topic: {topic}\n"
        f"Previous mastery: {previous_mastery:.0%}\n\n"
        f"Student's question: {question}\n"
        f"Tutor's response: {tutor_response}"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=ASSESSMENT_PROMPT),
            HumanMessage(content=context),
        ])
        result = _parse_json(response.content)
        assessment = {
            "understanding_score": max(
                0.0, min(1.0, float(result.get("understanding_score", 0.4)))
            ),
            "confidence": max(
                0.0, min(1.0, float(result.get("confidence", 0.5)))
            ),
            "misconceptions": result.get("misconceptions", []),
            "recommendation": result.get(
                "recommendation", "Continue practicing."
            ),
        }
    except Exception:
        assessment = {
            "understanding_score": 0.4,
            "confidence": 0.3,
            "misconceptions": [],
            "recommendation": "Continue exploring this topic.",
        }

    # Update mastery in SQLite
    update_mastery(
        student_id, topic,
        assessment["understanding_score"],
        assessment["confidence"],
    )
    current_mastery = get_mastery_for_topic(student_id, topic)

    # Build mastery dict
    mastery_dict = {}
    if profile and profile.get("mastery_scores"):
        mastery_dict = {
            t: info["score"]
            for t, info in profile["mastery_scores"].items()
        }
    mastery_dict[topic] = current_mastery

    return {
        "assessment": assessment,
        "mastery_scores": mastery_dict,
        "quiz": None,
    }


def _handle_quiz(
    state: dict, student_id: str, profile: Optional[Dict]
) -> dict:
    """Generate quiz questions tailored to the student's level."""
    question = state.get("question", "")

    # Detect topic from the quiz request
    topic = detect_topic(question, "")
    mastery = get_mastery_for_topic(student_id, topic)

    context = (
        f"Topic: {topic}\n"
        f"Student mastery level: {mastery:.0%}\n"
        f"Student request: {question}"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=QUIZ_PROMPT),
            HumanMessage(content=context),
        ])
        quiz = _parse_json(response.content)
        if not isinstance(quiz, list):
            quiz = [quiz]
    except Exception:
        quiz = [
            {
                "question": f"Explain the concept of {topic} in your own words.",
                "options": [
                    "A) I can explain it clearly",
                    "B) I have a basic idea",
                    "C) I'm not sure",
                    "D) I don't know yet",
                ],
                "correct_answer": "A) I can explain it clearly",
            }
        ]

    assessment = {
        "understanding_score": mastery,
        "confidence": 0.5,
        "misconceptions": [],
        "recommendation": f"Complete this quiz on {topic} to test your understanding.",
    }

    # Build mastery dict
    mastery_dict = {}
    if profile and profile.get("mastery_scores"):
        mastery_dict = {
            t: info["score"]
            for t, info in profile["mastery_scores"].items()
        }

    return {
        "assessment": assessment,
        "mastery_scores": mastery_dict,
        "quiz": quiz,
        "topic": topic,
    }
