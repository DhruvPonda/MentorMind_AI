from fastapi import APIRouter, HTTPException, Depends

from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.auth_service import get_current_student
from backend.agents.mentor_graph import run_mentor_graph

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_student: dict = Depends(get_current_student),
):
    """Multi-agent chat endpoint powered by LangGraph.

    Routes through: Supervisor → Tutor/Assessment/Planner/Report
    based on the student's intent.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    student_id = current_student["student_id"]

    # Execute the full multi-agent graph
    result = run_mentor_graph(student_id, request.question)

    # Determine the main answer based on the route taken
    route = result.get("route", "chat")

    if route == "report":
        answer = result.get("report", "Unable to generate report.")
    elif route == "plan":
        learning_path = result.get("learning_path", [])
        if learning_path:
            lines = ["Here's your recommended study plan:\n"]
            for i, step in enumerate(learning_path, 1):
                topic = step.get("topic", "")
                reason = step.get("reason", "")
                prereq = "✅" if step.get("prerequisite_met", True) else "⚠️"
                lines.append(f"{i}. {prereq} **{topic}** — {reason}")
            answer = "\n".join(lines)
        else:
            answer = "No specific study plan available yet. Keep learning!"
    elif route == "quiz":
        answer = "Here's your quiz! Answer the questions below."
    else:  # chat
        answer = result.get("tutor_response", "I couldn't generate a response.")

    return ChatResponse(
        answer=answer,
        topic=result.get("topic", "general"),
        mastery_scores=result.get("mastery_scores", {}),
        next_topics=result.get("next_topics", []),
        quiz=result.get("quiz"),
        report=result.get("report"),
        learning_path=result.get("learning_path", []),
    )
