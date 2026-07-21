"""Supervisor Agent: classifies student intent and routes to the correct pipeline."""

import os
from typing import Literal

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    api_key=os.getenv("GROQ_API_KEY"),
)


class SupervisorDecision(BaseModel):
    """Structured output for the supervisor's routing decision."""

    route: Literal["chat", "quiz", "report", "plan"] = Field(
        description=(
            "The type of request: 'chat' for learning questions, "
            "'quiz' for quiz/test requests, 'report' for progress reports, "
            "'plan' for study plan or next-topic requests."
        )
    )
    reasoning: str = Field(
        description="Brief explanation of why this route was chosen."
    )


SUPERVISOR_PROMPT = """You are the Supervisor Agent for MentorMind AI, an intelligent tutoring system.

Your job is to classify the student's intent into exactly one category:

- **chat**: The student is asking a learning question, wants an explanation, or is having a tutoring conversation. This is the DEFAULT.
- **quiz**: The student explicitly wants to be quizzed, tested, or wants practice questions on a topic. Look for words like "quiz", "test me", "practice questions", "assess me".
- **report**: The student wants to see their progress report, performance summary, or learning analytics. Look for words like "report", "progress", "how am I doing", "summary".
- **plan**: The student wants to know what to study next, wants a learning roadmap, or asks for topic recommendations. Look for words like "what should I study", "what's next", "recommend", "learning path".

Default to "chat" if the intent is ambiguous or doesn't clearly match quiz/report/plan.

Classify the following student message."""


def supervisor_node(state: dict) -> dict:
    """Classify student intent and decide which agents should execute."""
    question = state.get("question", "")

    try:
        structured_llm = llm.with_structured_output(SupervisorDecision)
        decision = structured_llm.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=question),
        ])
        return {"route": decision.route}
    except Exception:
        # Default to chat on any failure
        return {"route": "chat"}
