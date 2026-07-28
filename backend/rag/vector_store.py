"""Vector Store: ChromaDB collection for NCERT curriculum content."""

import json
import os
import uuid
import logging
from typing import List, Dict

import chromadb

from backend.rag.embedder import get_embedding_function

logger = logging.getLogger(__name__)

CHROMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "chroma_data"
)
COLLECTION_NAME = "curriculum_rag"

_client = None
_collection = None


def _get_client() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB PersistentClient."""
    global _client
    if _client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_rag_collection():
    """Return the curriculum_rag collection (creates if needed)."""
    global _collection
    if _collection is None:
        client = _get_client()
        embedding_fn = get_embedding_function()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(chunks: List[Dict], batch_size: int = 100) -> int:
    """Add document chunks to the vector store in batches.

    Args:
        chunks: List of {"text": ..., "metadata": {...}} from chunker.
        batch_size: Number of chunks per batch insert.

    Returns:
        Total number of chunks added.
    """
    collection = get_rag_collection()
    total_added = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        ids = [str(uuid.uuid4()) for _ in batch]
        documents = [c["text"] for c in batch]
        metadatas = []
        for c in batch:
            meta = {k: v for k, v in c["metadata"].items()}
            # Ensure all metadata values are ChromaDB-compatible types
            for key, val in list(meta.items()):
                if isinstance(val, (list, dict)):
                    meta[key] = json.dumps(val)
            metadatas.append(meta)

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        total_added += len(batch)
        logger.info(
            f"Added batch {i // batch_size + 1}: "
            f"{total_added}/{len(chunks)} chunks"
        )

    return total_added


def clear_collection() -> None:
    """Delete and recreate the RAG collection."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted collection: {COLLECTION_NAME}")
    except Exception:
        pass
    _collection = None


def get_collection_stats() -> Dict:
    """Return collection statistics."""
    collection = get_rag_collection()
    return {
        "name": COLLECTION_NAME,
        "count": collection.count(),
    }
