"""
Query service: RAG pipeline with ScaleDown optimization.

Flow:
    User query
        ↓
    Vector DB retrieval (embed query → top-k chunks)
        ↓
    Build raw context string from chunks
        ↓
    ScaleDown optimization (compress context)
        ↓
    LLM response via OpenRouter
        ↓
    Return answer + sources + metrics
"""
import logging
import time
from typing import List, Dict, Any
import httpx

from ..config.settings import settings
from ..retrieval.retriever import retrieve_chunks, build_context_from_chunks
from ..optimization.scaledown_pipeline import get_optimizer

logger = logging.getLogger(__name__)

RAG_SYSTEM_PROMPT = """You are CivicLens, an AI civic intelligence assistant specialized in Indian government policies and legislation.

Answer questions clearly and accurately based on the provided policy context.
- Be concise but complete
- Cite specific policies or acts when relevant
- If the context doesn't contain enough information, say so honestly
- Format your answer in clear paragraphs"""

RAG_USER_TEMPLATE = """Based on the following policy documents, answer this question:

Question: {query}

Policy Context:
{context}

Provide a clear, helpful answer for a citizen."""


async def answer_query(
    query: str,
    top_k: int = 5,
    db=None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline with ScaleDown optimization.

    Returns:
        answer: str
        sources: list of source policy metadata
        metrics: compression and token usage metrics
        latency_ms: total response time
    """
    start_time = time.time()

    # Step 1: Retrieve relevant chunks
    chunks = retrieve_chunks(query, top_k=top_k)
    if not chunks:
        return {
            "answer": (
                "I don't have specific information about that topic in my current "
                "knowledge base. Please try rephrasing your question or upload relevant documents."
            ),
            "sources": [],
            "metrics": {},
            "latency_ms": (time.time() - start_time) * 1000,
        }

    # Step 2: Build raw context
    raw_context = build_context_from_chunks(chunks, max_chars=6000)

    # Step 3: ScaleDown optimization
    optimizer = get_optimizer()
    optimized_context, opt_metrics = optimizer.compress_context(raw_context, query)

    # Step 4: LLM call via OpenRouter
    prompt = RAG_USER_TEMPLATE.format(query=query, context=optimized_context)
    answer = await _call_llm(prompt)

    latency_ms = (time.time() - start_time) * 1000

    # Step 5: Deduplicate sources
    seen_policy_ids = set()
    sources = []
    for chunk in chunks:
        pid = chunk.get("policy_id", "")
        if pid and pid not in seen_policy_ids:
            seen_policy_ids.add(pid)
            sources.append({
                "policy_id": pid,
                "title": chunk.get("title", ""),
                "source": chunk.get("source", ""),
                "score": round(chunk.get("score", 0.0), 3),
            })

    # Step 6: Log to DB
    if db is not None:
        _log_query(
            db=db,
            query=query,
            answer=answer,
            source_ids=list(seen_policy_ids),
            metrics=opt_metrics,
            latency_ms=latency_ms,
        )

    return {
        "answer": answer,
        "sources": sources,
        "metrics": opt_metrics,
        "latency_ms": round(latency_ms, 1),
    }


async def _call_llm(prompt: str) -> str:
    """Call OpenRouter LLM with the optimized context prompt."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://civiclens.app",
                    "X-Title": "CivicLens",
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {"role": "system", "content": RAG_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 1200,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            llm_content = data["choices"][0]["message"].get("content") or ""
            return llm_content.strip()

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return (
            "I encountered an issue while generating a response. "
            "Please try again in a moment."
        )


def _log_query(
    db,
    query: str,
    answer: str,
    source_ids: List[str],
    metrics: Dict,
    latency_ms: float,
) -> None:
    """Log query and ScaleDown metrics to DB."""
    try:
        from ..db.models import QueryLog
        log = QueryLog(
            query_text=query[:2000],
            answer_text=answer[:5000],
            source_policy_ids=source_ids,
            original_tokens=metrics.get("original_tokens", 0),
            compressed_tokens=metrics.get("compressed_tokens", 0),
            compression_ratio=metrics.get("compression_ratio", 1.0),
            savings_percent=metrics.get("savings_percent", 0.0),
            latency_ms=latency_ms,
            scaledown_used=not metrics.get("fallback", True),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.warning(f"Query log failed: {e}")
