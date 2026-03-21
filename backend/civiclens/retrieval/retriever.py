"""RAG retriever: embed query → fetch relevant chunks from vector store."""
import logging
from typing import List, Dict

from ..embeddings.embedder import embed_query
from ..vectorstore.vector_client import get_vector_store

logger = logging.getLogger(__name__)


def retrieve_chunks(query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve the most relevant policy chunks for a given query.

    Returns list of dicts with:
        - text: chunk content
        - policy_id: parent policy id
        - title: policy title
        - source: PRS | PIB | Gazette | Upload
        - score: similarity score (0-1)
    """
    try:
        query_embedding = embed_query(query)
        store = get_vector_store()
        results = store.query(query_embedding, top_k=top_k)

        chunks = []
        for r in results:
            meta = r.get("metadata", {})
            chunks.append({
                "text": meta.get("text", ""),
                "policy_id": meta.get("policy_id", ""),
                "title": meta.get("title", "Unknown Policy"),
                "source": meta.get("source", ""),
                "score": r.get("score", 0.0),
                "chunk_index": meta.get("chunk_index", 0),
            })

        return chunks

    except Exception as e:
        logger.error(f"Retrieval failed: {e}", exc_info=True)
        return []


def build_context_from_chunks(chunks: List[Dict], max_chars: int = 6000) -> str:
    """
    Concatenate retrieved chunks into a single context string for the LLM.
    Respects max_chars limit.
    """
    context_parts = []
    total_chars = 0

    for i, chunk in enumerate(chunks):
        header = f"[Source: {chunk['title']} ({chunk['source']})]"
        text = chunk["text"]
        part = f"{header}\n{text}"

        if total_chars + len(part) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 200:
                context_parts.append(part[:remaining])
            break

        context_parts.append(part)
        total_chars += len(part)

    return "\n\n---\n\n".join(context_parts)
