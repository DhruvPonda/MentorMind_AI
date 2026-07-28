"""Retriever: semantic search over NCERT curriculum content."""

import logging
from typing import List, Dict, Optional

from backend.rag.vector_store import get_rag_collection

logger = logging.getLogger(__name__)


def retrieve_documents(
    question: str,
    subject: Optional[str] = None,
    class_level: Optional[int] = None,
    n_results: int = 5,
) -> List[Dict]:
    """Retrieve the most relevant NCERT chunks for a question.

    Args:
        question: The student's question text.
        subject: Optional filter by subject (e.g., "mathematics").
        class_level: Optional filter by class (e.g., 9).
        n_results: Number of chunks to return.

    Returns:
        List of dicts with "text", "metadata", and "distance".
    """
    collection = get_rag_collection()

    if collection.count() == 0:
        logger.debug("RAG collection is empty — skipping retrieval")
        return []

    # Build where filter
    where_filter = None
    conditions = []

    if subject:
        conditions.append({"subject": subject.lower()})
    if class_level:
        conditions.append({"class_level": class_level})

    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    try:
        query_kwargs = {
            "query_texts": [question],
            "n_results": min(n_results, collection.count()),
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = collection.query(**query_kwargs)
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return []

    documents = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            documents.append({
                "text": doc,
                "metadata": (
                    results["metadatas"][0][i]
                    if results["metadatas"]
                    else {}
                ),
                "distance": (
                    results["distances"][0][i]
                    if results["distances"]
                    else None
                ),
            })

    logger.info(
        f"Retrieved {len(documents)} RAG chunks for: {question[:50]}..."
    )
    return documents


def build_rag_context(documents: List[Dict]) -> str:
    """Format retrieved chunks into a prompt-ready context string.

    Args:
        documents: Retrieved chunks from retrieve_documents().

    Returns:
        Formatted markdown string for LLM prompt injection.
    """
    if not documents:
        return ""

    parts = ["## Relevant Textbook Content\n"]
    parts.append(
        "Use the following NCERT textbook excerpts to answer the "
        "student's question. Cite the source when using this content.\n"
    )

    for i, doc in enumerate(documents, 1):
        meta = doc.get("metadata", {})
        source_parts = []
        if meta.get("subject"):
            source_parts.append(meta["subject"].title())
        if meta.get("class_level"):
            source_parts.append(f"Class {meta['class_level']}")
        if meta.get("chapter"):
            source_parts.append(meta["chapter"])
        if meta.get("page"):
            source_parts.append(f"Page {meta['page']}")

        source = " | ".join(source_parts) if source_parts else "Unknown source"
        parts.append(f"### Source {i}: {source}\n{doc['text']}\n")

    return "\n".join(parts)
