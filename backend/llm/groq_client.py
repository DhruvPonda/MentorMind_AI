import os
from typing import Dict, List, Optional

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

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


def build_system_prompt(
    student_profile: Optional[Dict] = None,
    strengths: Optional[List[str]] = None,
    weaknesses: Optional[List[str]] = None,
    mastery_scores: Optional[Dict] = None,
) -> str:
    """Build a dynamic system prompt incorporating student context."""
    prompt_parts = [BASE_SYSTEM_PROMPT]

    if student_profile:
        name = student_profile.get("name", "Student")
        prompt_parts.append(
            f"\n\n## Student Profile\nYou are tutoring {name}."
        )

    if strengths:
        prompt_parts.append(
            f"\n\n## Student Strengths\n"
            f"The student is strong in: {', '.join(strengths)}. "
            f"You can use these as building blocks for new concepts."
        )

    if weaknesses:
        prompt_parts.append(
            f"\n\n## Student Weaknesses\n"
            f"The student needs more help with: {', '.join(weaknesses)}. "
            f"Be extra patient and provide more examples when these topics come up."
        )

    if mastery_scores:
        scores_str = "\n".join(
            f"- {topic}: {info['score']:.0%} ({info['question_count']} questions)"
            for topic, info in mastery_scores.items()
        )
        prompt_parts.append(
            f"\n\n## Current Mastery Scores\n{scores_str}"
        )

    return "\n".join(prompt_parts)


def generate_response(
    question: str,
    student_profile: Optional[Dict] = None,
    memory_context: str = "",
) -> str:
    """
    Generate a context-aware response using the student profile and
    retrieved memories to personalize the tutoring experience.
    """
    try:
        # Build dynamic system prompt
        system_prompt = build_system_prompt(
            student_profile=student_profile,
            strengths=(
                student_profile.get("strengths") if student_profile else None
            ),
            weaknesses=(
                student_profile.get("weaknesses") if student_profile else None
            ),
            mastery_scores=(
                student_profile.get("mastery_scores")
                if student_profile
                else None
            ),
        )

        # Build user message with memory context
        user_content = ""
        if memory_context:
            user_content += f"{memory_context}\n\n---\n\n"
        user_content += f"Student's Question: {question}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.5,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error connecting to Groq API: {str(e)}"
