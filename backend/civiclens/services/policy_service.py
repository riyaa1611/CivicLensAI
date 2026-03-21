"""Policy service: ingestion, storage, and retrieval of policies."""
import asyncio
import logging
import uuid
from datetime import datetime
from functools import partial
from typing import List, Optional, Dict, Any

from ..db.database import db_session
from ..db.models import Policy
from ..processing.cleaner import clean_text
from ..processing.section_splitter import split_into_chunks
from ..embeddings.embedder import embed_batch
from ..vectorstore.vector_client import get_vector_store
from ..llm.analyzer import analyze_policy
from ..llm.classifier import classify_policy

logger = logging.getLogger(__name__)


async def ingest_policies(raw_policies: List[Dict]) -> Dict[str, int]:
    """
    Full ingestion pipeline for a list of scraped policy dicts.
    Each dict must have: title, source, date, description, link, raw_content.

    Returns stats: {ingested, skipped, failed}
    """
    stats = {"ingested": 0, "skipped": 0, "failed": 0}

    for raw in raw_policies:
        try:
            link = raw.get("link", "")

            # Duplicate check
            with db_session() as db:
                existing = db.query(Policy).filter(Policy.link == link).first()
                if existing:
                    stats["skipped"] += 1
                    continue

            # Clean text
            content = clean_text(raw.get("raw_content") or raw.get("description") or "")
            if not content:
                stats["skipped"] += 1
                continue

            # LLM analysis (summary + key clauses) — graceful fallback on failure
            try:
                analysis = await analyze_policy(content, raw.get("title", ""))
            except Exception as llm_err:
                logger.warning(f"LLM analysis failed for '{raw.get('title', '?')}': {llm_err} — using content fallback")
                sentences = [s.strip() for s in content.replace("\n", " ").split(".") if len(s.strip()) > 20]
                analysis = {
                    "summary": ". ".join(sentences[:4]) + "." if sentences else content[:400],
                    "key_clauses": sentences[4:8] if len(sentences) > 4 else [],
                }
            try:
                tags = await classify_policy(content, raw.get("title", ""))
            except Exception as tag_err:
                logger.warning(f"LLM classification failed for '{raw.get('title', '?')}': {tag_err} — using empty tags")
                tags = []

            # Save to DB
            policy_id = str(uuid.uuid4())
            date_val = raw.get("date")
            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val)
                except ValueError:
                    date_val = datetime.utcnow()

            policy = Policy(
                id=policy_id,
                title=raw["title"][:500],
                source=raw.get("source", "Unknown"),
                date=date_val,
                summary=analysis["summary"],
                key_clauses=analysis["key_clauses"],
                tags=tags,
                link=link,
                raw_content=content[:50000],
                is_indexed=False,
            )

            with db_session() as db:
                db.add(policy)

            # Embed and store in vector DB
            await _embed_and_store(policy_id, content, raw["title"], raw.get("source", ""))

            # Mark as indexed
            with db_session() as db:
                db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if db_policy:
                    db_policy.is_indexed = True

            stats["ingested"] += 1
            logger.info(f"Ingested: {raw['title'][:60]}")

        except Exception as e:
            logger.error(f"Failed to ingest policy '{raw.get('title', '?')}': {e}")
            stats["failed"] += 1

    return stats


async def _embed_and_store(
    policy_id: str, content: str, title: str, source: str
) -> None:
    """Embed policy chunks and store in vector database."""
    chunks = split_into_chunks(
        content,
        chunk_size=600,
        overlap=80,
        policy_id=policy_id,
        title=title,
    )
    if not chunks:
        return

    texts = [c["text"] for c in chunks]
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(None, partial(embed_batch, texts))

    store = get_vector_store()
    vectors = []
    for chunk, emb in zip(chunks, embeddings):
        chunk_id = f"{policy_id}_{chunk['chunk_index']}"
        metadata = {
            "text": chunk["text"][:1000],
            "policy_id": policy_id,
            "title": title,
            "source": source,
            "chunk_index": chunk["chunk_index"],
        }
        vectors.append((chunk_id, emb, metadata))

    store.upsert(vectors)
    logger.debug(f"Stored {len(vectors)} chunks for policy {policy_id}")


def get_policies(
    db,
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[datetime] = None,
) -> List[Policy]:
    """Fetch paginated policies from DB, optionally filtered."""
    query = db.query(Policy)

    if source:
        query = query.filter(Policy.source == source)

    if tag:
        # JSON contains filter — SQLite compatible
        query = query.filter(Policy.tags.like(f'%"{tag}"%'))

    if date_from:
        query = query.filter(Policy.date >= date_from)

    return (
        query.order_by(Policy.date.desc(), Policy.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_policy_by_id(db, policy_id: str) -> Optional[Policy]:
    """Fetch a single policy by ID."""
    return db.query(Policy).filter(Policy.id == policy_id).first()


def get_stats(db) -> Dict[str, Any]:
    """Compute dashboard stats from DB."""
    from sqlalchemy import func
    from ..db.models import QueryLog

    total_policies = db.query(func.count(Policy.id)).scalar() or 0
    total_queries = db.query(func.count(QueryLog.id)).scalar() or 0

    avg_ratio = (
        db.query(func.avg(QueryLog.compression_ratio))
        .filter(QueryLog.scaledown_used == True)
        .scalar()
    ) or 1.0

    total_savings = (
        db.query(func.sum(QueryLog.original_tokens - QueryLog.compressed_tokens))
        .filter(QueryLog.scaledown_used == True)
        .scalar()
    ) or 0

    source_counts = dict(
        db.query(Policy.source, func.count(Policy.id))
        .group_by(Policy.source)
        .all()
    )

    return {
        "total_policies": total_policies,
        "total_queries": total_queries,
        "avg_compression_ratio": round(float(avg_ratio), 2),
        "total_token_savings": int(total_savings),
        "source_counts": source_counts,
        "indexed_policies": db.query(func.count(Policy.id))
        .filter(Policy.is_indexed == True)
        .scalar() or 0,
    }
