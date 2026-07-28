"""Ingestion script: processes NCERT PDFs and stores them in ChromaDB."""

import os
import sys
import time
import logging
import argparse

# Add project root to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)

from backend.rag.pdf_loader import load_pdfs
from backend.rag.chunker import chunk_documents
from backend.rag.vector_store import (
    add_chunks,
    clear_collection,
    get_collection_stats,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest NCERT PDFs into ChromaDB for RAG"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Root directory containing NCERT PDFs (default: data/)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=600,
        help="Chunk size in words (default: 600)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=120,
        help="Chunk overlap in words (default: 120)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collection before ingesting",
    )
    args = parser.parse_args()

    print("\n[RAG] NCERT RAG Ingestion")
    print("-" * 40)
    print(f"[DIR] Data directory: {args.data_dir}")

    if not os.path.exists(args.data_dir):
        print(f"[ERROR] Data directory not found: {args.data_dir}")
        print(f"   Create the directory and add NCERT PDFs:")
        print(f"   {args.data_dir}/class9/mathematics/chapter1.pdf")
        sys.exit(1)

    if args.clear:
        print("[CLEAR] Clearing existing collection...")
        clear_collection()

    # Step 1: Load PDFs
    print("\n[STEP 1] Loading PDFs...")
    t0 = time.time()
    documents = load_pdfs(args.data_dir)
    load_time = time.time() - t0

    if not documents:
        print("[ERROR] No PDF pages found. Add PDFs to the data directory.")
        sys.exit(1)

    pdf_files = set(d["metadata"]["source_file"] for d in documents)
    print(f"   PDFs found: {len(pdf_files)}")
    print(f"   Pages extracted: {len(documents)}")
    print(f"   Time: {load_time:.1f}s")

    # Step 2: Chunk documents
    print("\n[STEP 2] Chunking documents...")
    t1 = time.time()
    chunks = chunk_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    chunk_time = time.time() - t1
    print(f"   Chunks created: {len(chunks)}")
    print(f"   Time: {chunk_time:.1f}s")

    # Step 3: Store in ChromaDB
    print("\n[STEP 3] Storing in ChromaDB...")
    t2 = time.time()
    stored = add_chunks(chunks)
    store_time = time.time() - t2
    print(f"   Chunks stored: {stored}")
    print(f"   Time: {store_time:.1f}s")

    # Summary
    total_time = time.time() - t0
    stats = get_collection_stats()

    print("\n" + "-" * 40)
    print("[DONE] Ingestion Complete!")
    print(f"   PDFs processed: {len(pdf_files)}")
    print(f"   Pages extracted: {len(documents)}")
    print(f"   Chunks created: {len(chunks)}")
    print(f"   Total in collection: {stats['count']}")
    print(f"   Total time: {total_time:.1f}s")
    print()


if __name__ == "__main__":
    main()
