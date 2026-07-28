"""RAG search endpoint for direct document retrieval."""

from fastapi import APIRouter, Depends

from backend.models.schemas import RAGSearchRequest, RAGSearchResponse
from backend.services.auth_service import get_current_student
from backend.rag.retriever import retrieve_documents

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/search", response_model=RAGSearchResponse)
async def rag_search(
    request: RAGSearchRequest,
    current_student: dict = Depends(get_current_student),
):
    """Search NCERT curriculum content using semantic similarity.

    Returns the top-N most relevant textbook chunks for the given question,
    optionally filtered by subject and class level.
    """
    documents = retrieve_documents(
        question=request.question,
        subject=request.subject,
        class_level=request.class_level,
        n_results=request.n_results,
    )

    return RAGSearchResponse(
        documents=documents,
        query=request.question,
        count=len(documents),
    )
