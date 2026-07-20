import chromadb
import os
import uuid
from typing import List, Dict

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "chroma_data")

_client = None
_collection = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Return a singleton ChromaDB PersistentClient."""
    global _client
    if _client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_collection():
    """Return the conversation_memories collection (creates if needed)."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="conversation_memories",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_memory(document: str, metadata: Dict) -> str:
    """
    Store a conversation memory with metadata in ChromaDB.
    Returns the generated memory ID.
    """
    collection = get_collection()
    memory_id = str(uuid.uuid4())
    collection.add(
        ids=[memory_id],
        documents=[document],
        metadatas=[metadata]
    )
    return memory_id


def query_memories(query_text: str, student_id: str, n_results: int = 5) -> List[Dict]:
    """
    Retrieve the top-N semantically similar memories for a student.
    Uses ChromaDB's built-in embedding (all-MiniLM-L6-v2).
    """
    collection = get_collection()

    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"student_id": student_id}
        )
    except Exception:
        return []

    memories = []
    if results and results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            memories.append({
                "document": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            })
    return memories


def get_student_memories(student_id: str, n_results: int = 10) -> List[Dict]:
    """Retrieve recent memories for a student (unordered)."""
    collection = get_collection()
    try:
        results = collection.get(
            where={"student_id": student_id},
            limit=n_results
        )
    except Exception:
        return []

    memories = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"]):
            memories.append({
                "document": doc,
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
    return memories
