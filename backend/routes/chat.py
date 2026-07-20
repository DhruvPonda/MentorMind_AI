from fastapi import APIRouter, HTTPException, Depends

from backend.models.schemas import ChatRequest, ChatResponse
from backend.llm.groq_client import generate_response
from backend.services.auth_service import get_current_student
from backend.services.student_profile import (
    get_student_profile,
    update_mastery,
    get_mastery_for_topic,
)
from backend.services.memory_service import (
    retrieve_memories,
    store_memory,
    build_memory_context,
)
from backend.services.topic_detector import detect_topic
from backend.services.assessment_agent import assess_understanding

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_student: dict = Depends(get_current_student),
):
    """Full memory-aware chat pipeline with mastery tracking."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    student_id = current_student["student_id"]

    # 1. Retrieve student profile
    profile = get_student_profile(student_id)

    # 2. Retrieve similar past conversations from ChromaDB
    memories = retrieve_memories(student_id, request.question)
    memory_context = build_memory_context(memories)

    # 3. Generate context-aware response
    answer = generate_response(
        question=request.question,
        student_profile=profile,
        memory_context=memory_context,
    )

    # 4. Detect topic (hybrid: keyword → LLM fallback)
    topic = detect_topic(request.question, answer)

    # 5. Assess understanding via dedicated LLM agent
    previous_mastery = get_mastery_for_topic(student_id, topic)
    assessment = assess_understanding(
        question=request.question,
        answer=answer,
        topic=topic,
        previous_mastery=previous_mastery,
    )

    # 6. Update mastery scores in SQLite
    update_mastery(
        student_id=student_id,
        topic=topic,
        understanding_score=assessment["understanding_score"],
        confidence=assessment["confidence"],
    )

    # 7. Store conversation memory in ChromaDB
    current_mastery = get_mastery_for_topic(student_id, topic)
    store_memory(
        student_id=student_id,
        question=request.question,
        answer=answer,
        topic=topic,
        mastery_score=current_mastery,
    )

    # 8. Build response with mastery scores
    mastery_dict = {}
    if profile and profile.get("mastery_scores"):
        mastery_dict = {
            t: info["score"]
            for t, info in profile["mastery_scores"].items()
        }
    mastery_dict[topic] = current_mastery

    return ChatResponse(
        answer=answer,
        topic=topic,
        mastery_scores=mastery_dict,
    )
