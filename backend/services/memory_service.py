from datetime import datetime, timezone
from typing import List, Dict

from backend.memory.chroma_manager import add_memory, query_memories


def retrieve_memories(
    student_id: str, question: str, n_results: int = 5
) -> List[Dict]:
    """Retrieve semantically similar past conversations for a student."""
    return query_memories(
        query_text=question, student_id=student_id, n_results=n_results
    )


def store_memory(
    student_id: str,
    question: str,
    answer: str,
    topic: str,
    mastery_score: float,
) -> str:
    """
    Store a new conversation memory in ChromaDB.
    Returns the generated memory ID.
    """
    document = f"Student asked: {question}\n\nTutor responded: {answer}"

    metadata = {
        "student_id": student_id,
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mastery_score": mastery_score,
    }

    return add_memory(document=document, metadata=metadata)


def build_memory_context(memories: List[Dict]) -> str:
    """
    Format retrieved memories into a prompt-friendly context string
    that can be injected into the LLM conversation.
    """
    if not memories:
        return ""

    context_parts = ["## Previous Relevant Conversations\n"]

    for i, memory in enumerate(memories, 1):
        doc = memory.get("document", "")
        meta = memory.get("metadata", {})
        topic = meta.get("topic", "unknown")
        timestamp = meta.get("timestamp", "unknown")
        mastery = meta.get("mastery_score", "N/A")

        context_parts.append(
            f"### Memory {i} (Topic: {topic}, Mastery at time: {mastery})\n"
            f"{doc}\n"
        )

    return "\n".join(context_parts)
