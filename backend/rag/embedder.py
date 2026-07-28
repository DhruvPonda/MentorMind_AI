"""Embedder: provides the embedding function for the RAG vector store."""

import logging

from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

logger = logging.getLogger(__name__)

_embedding_fn = None


def get_embedding_function() -> SentenceTransformerEmbeddingFunction:
    """Return a singleton SentenceTransformer embedding function.

    Uses all-MiniLM-L6-v2 for generating document and query embeddings.
    This is explicitly configured for the RAG collection to allow
    easy swapping of embedding models in the future.
    """
    global _embedding_fn
    if _embedding_fn is None:
        logger.info(
            "Initializing SentenceTransformer embedding function "
            "(all-MiniLM-L6-v2)"
        )
        _embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embedding_fn
