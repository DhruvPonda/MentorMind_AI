"""MentorMind LangGraph: assembles and compiles the multi-agent StateGraph."""

from langgraph.graph import StateGraph, START, END

from backend.agents.mentor_state import MentorState
from backend.agents.supervisor_agent import supervisor_node
from backend.agents.tutor_agent import tutor_node
from backend.agents.assessment_agent import assessment_node
from backend.agents.planner_agent import planner_node
from backend.agents.report_agent import report_node
from backend.services.memory_service import (
    retrieve_memories,
    store_memory,
    build_memory_context,
)
from backend.services.student_profile import get_student_profile


# ─── Utility Nodes ──────────────────────────────────────────────────


def retrieve_context_node(state: dict) -> dict:
    """Fetch student profile from SQLite and similar memories from ChromaDB."""
    student_id = state.get("student_id", "")
    question = state.get("question", "")

    profile = get_student_profile(student_id)
    memories = retrieve_memories(student_id, question)
    memory_context = build_memory_context(memories)

    return {
        "student_profile": profile,
        "memories": memories,
        "memory_context": memory_context,
    }


def store_memory_node(state: dict) -> dict:
    """Persist conversation memory to ChromaDB after the pipeline completes."""
    student_id = state.get("student_id", "")
    question = state.get("question", "")
    route = state.get("route", "chat")
    topic = state.get("topic", "general")
    mastery_scores = state.get("mastery_scores", {})
    current_mastery = mastery_scores.get(topic, 0.0)

    # Determine content to store based on the route
    if route == "chat":
        content = state.get("tutor_response", "")
    elif route == "quiz":
        import json

        quiz = state.get("quiz", [])
        content = f"Quiz generated on {topic}: {json.dumps(quiz)}"
    elif route == "plan":
        next_topics = state.get("next_topics", [])
        content = f"Study plan requested. Recommended: {', '.join(next_topics)}"
    else:
        content = ""

    if content and student_id:
        store_memory(
            student_id=student_id,
            question=question,
            answer=content,
            topic=topic,
            mastery_score=current_mastery,
        )

    return {}


# ─── Routing Functions ──────────────────────────────────────────────


def route_from_supervisor(state: dict) -> str:
    """Route to the correct pipeline based on the supervisor's decision."""
    return state.get("route", "chat")


# ─── Graph Assembly ─────────────────────────────────────────────────


def build_mentor_graph() -> StateGraph:
    """Assemble and compile the full multi-agent StateGraph."""
    builder = StateGraph(MentorState)

    # Register utility nodes
    builder.add_node("retrieve_context", retrieve_context_node)
    builder.add_node("store_memory", store_memory_node)

    # Register agent nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("tutor", tutor_node)
    builder.add_node("assessment", assessment_node)
    builder.add_node("planner", planner_node)
    builder.add_node("report", report_node)

    # ─── Edges ──────────────────────────────────────────────────

    # Entry: always retrieve context first
    builder.add_edge(START, "retrieve_context")
    builder.add_edge("retrieve_context", "supervisor")

    # Supervisor routes conditionally
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "chat": "tutor",
            "quiz": "assessment",
            "report": "report",
            "plan": "planner",
        },
    )

    # Chat pipeline: tutor → assessment → planner → store_memory → END
    builder.add_edge("tutor", "assessment")

    # Both chat & quiz: assessment → planner → store_memory → END
    builder.add_edge("assessment", "planner")
    builder.add_edge("planner", "store_memory")
    builder.add_edge("store_memory", END)

    # Report: → END directly
    builder.add_edge("report", END)

    return builder.compile()


# Compiled graph (singleton)
mentor_graph = build_mentor_graph()


def run_mentor_graph(student_id: str, question: str) -> dict:
    """Execute the full multi-agent pipeline.

    Args:
        student_id: The authenticated student's UUID.
        question: The student's message/question.

    Returns:
        The final MentorState dict with all agent outputs.
    """
    initial_state: MentorState = {
        "student_id": student_id,
        "question": question,
        "student_profile": None,
        "memories": [],
        "memory_context": "",
        "route": "chat",
        "tutor_response": "",
        "topic": "general",
        "assessment": {},
        "mastery_scores": {},
        "quiz": None,
        "next_topics": [],
        "learning_path": [],
        "report": None,
    }

    final_state = mentor_graph.invoke(
        initial_state,
        {"recursion_limit": 15},
    )
    return final_state
