"""Tutor Agent: generates personalized explanations using student context and memories."""

import os
from typing import Dict, List, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.services.topic_detector import detect_topic

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.5,
    max_tokens=1024,
    api_key=os.getenv("GROQ_API_KEY"),
)

BASE_SYSTEM_PROMPT = """You are MentorMind AI, a friendly, knowledgeable, and adaptive AI tutor.

Core Teaching Rules:
1. Explain concepts in simple, clear language appropriate to the student's level.
2. Teach step-by-step, building on what the student already knows.
3. If the student is confused, provide examples and analogies.
4. Encourage learning and critical thinking instead of directly giving answers.
5. If the question is mathematical, show calculations step by step.
6. End explanations with a short summary.
7. Reference past conversations when relevant to show continuity.
8. Adapt your difficulty level based on the student's mastery scores."""


def _build_system_prompt(
    profile: Optional[Dict] = None,
    strengths: Optional[List[str]] = None,
    weaknesses: Optional[List[str]] = None,
    mastery_scores: Optional[Dict] = None,
) -> str:
    """Build a dynamic system prompt incorporating student context."""
    parts = [BASE_SYSTEM_PROMPT]

    if profile:
        name = profile.get("name", "Student")
        parts.append(f"\n\n## Student Profile\nYou are tutoring {name}.")

    if strengths:
        parts.append(
            f"\n\n## Student Strengths\n"
            f"Strong in: {', '.join(strengths)}. "
            f"Use these as building blocks for new concepts."
        )

    if weaknesses:
        parts.append(
            f"\n\n## Student Weaknesses\n"
            f"Needs help with: {', '.join(weaknesses)}. "
            f"Be extra patient and provide more examples."
        )

    if mastery_scores:
        scores_str = "\n".join(
            f"- {topic}: {info['score']:.0%} ({info['question_count']} questions)"
            for topic, info in mastery_scores.items()
        )
        parts.append(f"\n\n## Current Mastery Scores\n{scores_str}")

    return "\n".join(parts)


def tutor_node(state: dict) -> dict:
    """Generate a personalized explanation using student profile and memory context."""
    question = state.get("question", "")
    profile = state.get("student_profile")
    memory_context = state.get("memory_context", "")

    # Build dynamic system prompt
    system_prompt = _build_system_prompt(
        profile=profile,
        strengths=profile.get("strengths") if profile else None,
        weaknesses=profile.get("weaknesses") if profile else None,
        mastery_scores=profile.get("mastery_scores") if profile else None,
    )

    # Build user message with memory context
    user_content = ""
    if memory_context:
        user_content += f"{memory_context}\n\n---\n\n"
    user_content += f"Student's Question: {question}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ])
        tutor_response = response.content
    except Exception as e:
        tutor_response = f"I apologize, I encountered an error: {str(e)}"

    # Detect topic using existing hybrid detector
    topic = detect_topic(question, tutor_response)

    return {"tutor_response": tutor_response, "topic": topic}
