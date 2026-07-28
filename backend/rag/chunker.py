"""Chunker: splits extracted PDF text into overlapping chunks."""

import logging
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def chunk_documents(
    documents: List[Dict],
    chunk_size: int = 600,
    chunk_overlap: int = 120,
) -> List[Dict]:
    """Split documents into overlapping chunks with preserved metadata.

    Args:
        documents: List of {"text": ..., "metadata": {...}} from pdf_loader.
        chunk_size: Maximum number of words per chunk.
        chunk_overlap: Number of overlapping words between chunks.

    Returns:
        List of {"text": ..., "metadata": {...}} chunks with inherited metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda x: len(x.split()),
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )

    chunks = []

    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]

        splits = text_splitter.split_text(text)

        for i, chunk_text in enumerate(splits):
            if len(chunk_text.strip()) < 20:
                continue

            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(splits),
            }
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": chunk_metadata,
            })

    logger.info(f"Created {len(chunks)} chunks from {len(documents)} pages")
    return chunks
