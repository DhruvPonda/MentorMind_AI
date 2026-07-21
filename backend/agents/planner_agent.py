"""Planner Agent: recommends next topics using prerequisite relationships and mastery data."""

import os
import json
from typing import Dict, List

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_tokens=500,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ─── Prerequisite Knowledge Graph ───────────────────────────────────

PREREQUISITE_GRAPH = {
    "variables": [],
    "functions": ["variables"],
    "recursion": ["functions"],
    "dynamic programming": ["recursion", "algorithms"],
    "sorting algorithms": ["data structures", "algorithms"],
    "data structures": ["variables"],
    "algorithms": ["functions", "data structures"],
    "object-oriented programming": ["functions", "variables"],
    "machine learning": ["linear algebra", "statistics", "python programming"],
    "probability": ["statistics"],
    "statistics": ["calculus"],
    "calculus": ["linear algebra"],
    "linear algebra": [],
    "newton's laws": [],
    "thermodynamics": ["newton's laws"],
    "electromagnetism": ["calculus", "newton's laws"],
    "optics": ["electromagnetism"],
    "chemistry basics": [],
    "organic chemistry": ["chemistry basics"],
    "biology basics": [],
    "photosynthesis": ["biology basics", "chemistry basics"],
    "ecology": ["biology basics"],
    "evolution": ["biology basics"],
    "python programming": ["variables", "functions"],
    "web development": ["python programming"],
    "databases": ["data structures"],
}

PLANNER_PROMPT = """You are the Planner Agent for MentorMind AI. Recommend what the student should study next.

You have:
1. The student's current mastery scores
2. A prerequisite knowledge graph
3. The student's recent assessment results (including any misconceptions)

Rules:
1. Only recommend topics whose prerequisites the student has mastered (score >= 0.6).
2. Prioritize topics that are weak (< 0.5) or completely unstarted.
3. If a student has misconceptions, recommend revisiting the relevant prerequisite first.
4. Recommend exactly 3 topics.
5. Order them by priority (most important first).

Return ONLY a JSON object:
{
    "next_topics": ["topic1", "topic2", "topic3"],
    "learning_path": [
        {"topic": "topic1", "reason": "why this topic", "prerequisite_met": true},
        {"topic": "topic2", "reason": "why this topic", "prerequisite_met": true},
        {"topic": "topic3", "reason": "why this topic", "prerequisite_met": false}
    ]
}

IMPORTANT: Respond with ONLY valid JSON."""


def _get_ready_topics(mastery_scores: Dict[str, float]) -> List[Dict]:
    """Find topics where prerequisites are met but mastery is low or unstarted."""
    ready = []

    for topic, prereqs in PREREQUISITE_GRAPH.items():
        current_mastery = mastery_scores.get(topic, 0.0)

        # Skip already-mastered topics
        if current_mastery >= 0.7:
            continue

        # Check if all prerequisites are met
        prereqs_met = (
            all(mastery_scores.get(p, 0.0) >= 0.6 for p in prereqs)
            if prereqs
            else True
        )

        ready.append({
            "topic": topic,
            "current_mastery": current_mastery,
            "prerequisites_met": prereqs_met,
            "prerequisites": prereqs,
        })

    # Sort: prereqs met first, then by lowest mastery
    ready.sort(
        key=lambda x: (not x["prerequisites_met"], x["current_mastery"])
    )
    return ready


def planner_node(state: dict) -> dict:
    """Recommend next topics based on prerequisites and mastery scores."""
    assessment = state.get("assessment", {})
    mastery_scores = state.get("mastery_scores", {})
    topic = state.get("topic", "general")

    # Flatten mastery scores to {topic: score}
    mastery_flat = {}
    profile = state.get("student_profile")
    if profile and profile.get("mastery_scores"):
        for t, info in profile["mastery_scores"].items():
            mastery_flat[t] = (
                info["score"] if isinstance(info, dict) else info
            )
    mastery_flat.update(mastery_scores)

    # Get candidate topics from prerequisite graph
    ready_topics = _get_ready_topics(mastery_flat)

    # Build context for the LLM
    context = f"Current topic: {topic}\n"
    context += f"Assessment: {json.dumps(assessment)}\n\n"

    context += "Student mastery scores:\n"
    for t, s in mastery_flat.items():
        context += f"- {t}: {s:.0%}\n"

    context += "\nCandidate topics (from prerequisite graph):\n"
    for rt in ready_topics[:10]:
        context += (
            f"- {rt['topic']}: mastery={rt['current_mastery']:.0%}, "
            f"prereqs_met={rt['prerequisites_met']}, "
            f"prereqs={rt['prerequisites']}\n"
        )

    try:
        response = llm.invoke([
            SystemMessage(content=PLANNER_PROMPT),
            HumanMessage(content=context),
        ])

        result_text = response.content.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)
        next_topics = result.get("next_topics", [])[:3]
        learning_path = result.get("learning_path", [])[:3]
    except Exception:
        # Fallback: use the computed ready_topics
        top = ready_topics[:3]
        next_topics = [t["topic"] for t in top]
        learning_path = [
            {
                "topic": t["topic"],
                "reason": (
                    f"Mastery at {t['current_mastery']:.0%}, ready to learn"
                    if t["prerequisites_met"]
                    else f"Prerequisites needed: {', '.join(t['prerequisites'])}"
                ),
                "prerequisite_met": t["prerequisites_met"],
            }
            for t in top
        ]

    return {"next_topics": next_topics, "learning_path": learning_path}
