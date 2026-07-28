"""PDF Loader: recursively loads NCERT PDFs and extracts text with metadata."""

import os
import re
import logging
from typing import List, Dict

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """Clean extracted PDF text by removing excessive whitespace and artifacts."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def _extract_chapter_name(filename: str) -> str:
    """Extract chapter name from PDF filename.

    Examples:
        'Chapter_1_Number_Systems.pdf' -> 'Number Systems'
        'ch2_Polynomials.pdf' -> 'Polynomials'
        '03_Coordinate_Geometry.pdf' -> 'Coordinate Geometry'
    """
    name = os.path.splitext(filename)[0]
    name = re.sub(
        r'^(chapter|ch|unit)[-_\s]*\d+[-_\s]*', '', name, flags=re.IGNORECASE
    )
    name = re.sub(r'^\d+[-_\s]*', '', name)
    name = name.replace('_', ' ').replace('-', ' ')
    name = name.strip().title()
    return name if name else os.path.splitext(filename)[0]


def _extract_metadata(file_path: str, data_dir: str) -> Dict:
    """Parse class level, subject, and chapter from directory structure.

    Expected structure: data/class{N}/{subject}/filename.pdf
    """
    rel_path = os.path.relpath(file_path, data_dir)
    parts = rel_path.replace('\\', '/').split('/')

    metadata = {
        "source_file": rel_path.replace('\\', '/'),
        "class_level": 0,
        "subject": "general",
        "chapter": _extract_chapter_name(os.path.basename(file_path)),
    }

    if len(parts) >= 3:
        class_dir = parts[0].lower()
        class_match = re.search(r'(\d+)', class_dir)
        if class_match:
            metadata["class_level"] = int(class_match.group(1))
        metadata["subject"] = parts[1].lower()
    elif len(parts) >= 2:
        class_dir = parts[0].lower()
        class_match = re.search(r'(\d+)', class_dir)
        if class_match:
            metadata["class_level"] = int(class_match.group(1))

    return metadata


def load_pdfs(data_dir: str = "data") -> List[Dict]:
    """Recursively load all PDFs from the data directory.

    Args:
        data_dir: Root directory containing NCERT PDFs organized by class/subject.

    Returns:
        List of dicts with 'text' and 'metadata' for each page.
    """
    documents = []
    pdf_count = 0

    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found: {data_dir}")
        return documents

    for root, _, files in os.walk(data_dir):
        for filename in sorted(files):
            if not filename.lower().endswith('.pdf'):
                continue

            file_path = os.path.join(root, filename)
            base_metadata = _extract_metadata(file_path, data_dir)
            pdf_count += 1

            try:
                reader = PdfReader(file_path)
                logger.info(
                    f"Loading: {base_metadata['source_file']} "
                    f"({len(reader.pages)} pages)"
                )

                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if not text or len(text.strip()) < 50:
                        continue

                    cleaned = _clean_text(text)
                    if len(cleaned) < 50:
                        continue

                    page_metadata = {**base_metadata, "page": page_num}
                    documents.append({
                        "text": cleaned,
                        "metadata": page_metadata,
                    })
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

    logger.info(f"Loaded {len(documents)} pages from {pdf_count} PDFs")
    return documents
