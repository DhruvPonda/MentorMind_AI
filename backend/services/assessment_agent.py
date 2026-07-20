import os
import json
from typing import Dict, List, Optional

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

ASSESSMENT_PROMPT = """You are an educational assessment agent for MentorMind AI.
Your job is to evaluate whether a student understands a concept based on their interaction.

Analyze the conversation and return a JSON evaluation:
{
    "understanding_score": <float 0.0-1.0, where 0=no understanding, 1=complete mastery>,
    "confidence": <float 0.0-1.0, how confident you are in your assessment>,
    "misconceptions": [<list of identified misconceptions, empty if none>],
    "recommendation": "<brief suggestion for next steps>"
}

Assessment criteria:
- Basic "what is" question → moderate score (0.3-0.5)
- Follow-up showing deeper curiosity → higher score (0.5-0.7)
- Demonstrated application of the concept → high score (0.7-0.9)
- Corrected a previous misconception → boost score
- Showed confusion or asked for re-explanation → lower score (0.2-0.4)
- Consider the student's previous mastery score as context

IMPORTANT: Respond with ONLY valid JSON, no other text."""


def assess_understanding(
    question: str,
    answer: str,
    topic: str,
    previous_mastery: float = 0.0,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Use a dedicated LLM call to assess student understanding.

    Returns:
        Dict with keys: understanding_score, confidence, misconceptions, recommendation
    """
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Build assessment context
        context = f"Topic: {topic}\nPrevious mastery score: {previous_mastery}\n\n"

        if conversation_history:
            context += "Recent conversation history:\n"
            for msg in conversation_history[-4:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]
                context += f"- {role}: {content}\n"
            context += "\n"

        context += f"Student's question: {question}\nTutor's response: {answer}"

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": ASSESSMENT_PROMPT},
                {"role": "user", "content": context},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=300,
        )

        result_text = response.choices[0].message.content.strip()

        # Handle markdown code blocks the LLM might wrap the JSON in
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)

        # Validate and clamp values
        return {
            "understanding_score": max(
                0.0, min(1.0, float(result.get("understanding_score", 0.3)))
            ),
            "confidence": max(
                0.0, min(1.0, float(result.get("confidence", 0.5)))
            ),
            "misconceptions": result.get("misconceptions", []),
            "recommendation": result.get(
                "recommendation", "Continue practicing this topic."
            ),
        }

    except (json.JSONDecodeError, Exception):
        # Fallback: return a moderate default assessment
        return {
            "understanding_score": 0.4,
            "confidence": 0.3,
            "misconceptions": [],
            "recommendation": "Continue exploring this topic.",
        }
