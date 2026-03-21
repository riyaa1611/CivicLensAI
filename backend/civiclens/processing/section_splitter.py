"""Split long policy documents into sections for embedding."""
import re
from typing import List, Dict


def split_into_chunks(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
    policy_id: str = "",
    title: str = "",
) -> List[Dict]:
    """
    Split text into overlapping chunks suitable for embedding.

    Returns list of dicts with:
        - text: chunk content
        - chunk_index: position in document
        - policy_id: parent policy id
        - title: policy title
    """
    if not text:
        return []

    # First try to split on section headers
    sections = _split_by_sections(text)
    if len(sections) > 1:
        chunks = []
        for i, section in enumerate(sections):
            sub_chunks = _sliding_window(section, chunk_size, overlap)
            for j, chunk_text in enumerate(sub_chunks):
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": len(chunks),
                    "policy_id": policy_id,
                    "title": title,
                })
        return chunks

    # Fallback: sliding window on plain text
    raw_chunks = _sliding_window(text, chunk_size, overlap)
    return [
        {
            "text": chunk_text,
            "chunk_index": i,
            "policy_id": policy_id,
            "title": title,
        }
        for i, chunk_text in enumerate(raw_chunks)
    ]


def _split_by_sections(text: str) -> List[str]:
    """
    Try to split on common government document section patterns:
    - Numbered sections: "1.", "2.", "Section 1"
    - Clauses: "(a)", "(b)"
    - Capital headers
    """
    # Patterns like "Section 1", "1.", "SECTION 1"
    pattern = r"(?=\n(?:Section\s+\d+|SECTION\s+\d+|\d+\.\s+[A-Z]))"
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if len(p.strip()) > 50]


def _sliding_window(text: str, size: int, overlap: int) -> List[str]:
    """Split text into overlapping word-level windows."""
    words = text.split()
    if len(words) <= size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end == len(words):
            break
        start += size - overlap

    return chunks
