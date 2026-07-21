"""Shared state object for the MentorMind multi-agent graph."""

from typing import TypedDict, Optional, Dict, List


class MentorState(TypedDict, total=False):
    """Shared state flowing through all agents in the LangGraph pipeline.

    This TypedDict defines every field that agents can read from or write to.
    Using total=False makes all fields optional so nodes can return partial updates.
    """

    # ─── Input (set by the caller) ───────────────────────────────────
    student_id: str
    question: str

    # ─── Context (set by retrieve_context node) ─────────────────────
    student_profile: Optional[Dict]
    memories: List[Dict]
    memory_context: str

    # ─── Supervisor ─────────────────────────────────────────────────
    route: str  # "chat" | "quiz" | "report" | "plan"

    # ─── Tutor Agent ────────────────────────────────────────────────
    tutor_response: str
    topic: str

    # ─── Assessment Agent ───────────────────────────────────────────
    assessment: Dict  # {understanding_score, confidence, misconceptions, recommendation}
    mastery_scores: Dict[str, float]
    quiz: Optional[List[Dict]]  # [{question, options, correct_answer}]

    # ─── Planner Agent ──────────────────────────────────────────────
    next_topics: List[str]
    learning_path: List[Dict]  # [{topic, reason, prerequisite_met}]

    # ─── Report Agent ───────────────────────────────────────────────
    report: Optional[str]
