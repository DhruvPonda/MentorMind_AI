"""Report Agent: generates comprehensive progress reports for teachers and parents."""

import os
from typing import Dict

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.memory.chroma_manager import get_student_memories

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
    max_tokens=1024,
    api_key=os.getenv("GROQ_API_KEY"),
)

REPORT_PROMPT = """You are the Report Agent for MentorMind AI. Generate a comprehensive student progress report.

Format the report in clean Markdown with these sections:

## 📊 Progress Report for {student_name}

### Overview
Brief summary of the student's overall learning journey and engagement.

### 💪 Strengths
Topics where the student excels (mastery >= 70%). Mention specific scores.

### ⚠️ Areas for Improvement
Topics where the student needs more practice (mastery < 40%). Suggest specific strategies.

### 📈 Topic Breakdown
List all topics with their mastery percentages and question counts.

### 📝 Recent Activity
Summary of recent learning interactions and topics covered.

### 🎯 Recommendations
Specific, actionable suggestions for what the student should focus on next.

Be encouraging but honest. Use specific mastery percentages. Keep the tone professional
but warm — this report may be read by teachers or parents."""


def report_node(state: dict) -> dict:
    """Generate a comprehensive progress report from student data."""
    student_id = state.get("student_id", "")
    profile = state.get("student_profile")

    if not profile:
        return {
            "report": (
                "No student profile found. "
                "Please complete some learning sessions first."
            )
        }

    # Get recent conversation memories
    recent_memories = get_student_memories(student_id, n_results=10)

    # Build context for the LLM
    context = f"Student: {profile.get('name', 'Unknown')}\n"
    context += f"Account created: {profile.get('created_at', 'Unknown')}\n"
    context += f"Last active: {profile.get('last_active', 'Unknown')}\n\n"

    # Mastery scores
    context += "Mastery Scores:\n"
    mastery = profile.get("mastery_scores", {})
    if mastery:
        for topic, info in mastery.items():
            score = info["score"] if isinstance(info, dict) else info
            q_count = (
                info.get("question_count", 0)
                if isinstance(info, dict)
                else 0
            )
            context += f"- {topic}: {score:.0%} ({q_count} questions)\n"
    else:
        context += "- No mastery data yet.\n"

    # Strengths and weaknesses
    strengths = profile.get("strengths", [])
    weaknesses = profile.get("weaknesses", [])
    context += f"\nStrengths: {', '.join(strengths) or 'None identified yet'}\n"
    context += f"Weaknesses: {', '.join(weaknesses) or 'None identified yet'}\n\n"

    # Recent conversations
    context += "Recent Conversations:\n"
    if recent_memories:
        for i, mem in enumerate(recent_memories[:5], 1):
            doc = mem.get("document", "")[:200]
            mem_topic = mem.get("metadata", {}).get("topic", "unknown")
            context += f"{i}. [{mem_topic}] {doc}...\n"
    else:
        context += "No conversation history yet.\n"

    try:
        response = llm.invoke([
            SystemMessage(content=REPORT_PROMPT),
            HumanMessage(content=context),
        ])
        report = response.content
    except Exception as e:
        report = f"Error generating report: {str(e)}"

    return {"report": report}
