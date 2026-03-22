"""FastAPI route definitions for CivicLens API."""
import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import Policy
from ..services.policy_service import (
    get_policies, get_policy_by_id, get_stats, ingest_policies, _embed_and_store
)
from ..services.query_service import answer_query
from ..processing.cleaner import clean_text, extract_pdf_text
from ..llm.analyzer import analyze_policy
from ..llm.classifier import classify_policy
from ..ingestion.scheduler import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    metrics: dict
    latency_ms: float


class PolicyResponse(BaseModel):
    id: str
    title: str
    source: str
    date: Optional[str]
    summary: Optional[str]
    tags: List[str]
    key_clauses: List[str]
    link: Optional[str]
    is_indexed: bool
    created_at: Optional[str]


class DashboardResponse(BaseModel):
    total_policies: int
    total_queries: int
    avg_compression_ratio: float
    total_token_savings: int
    source_counts: dict
    indexed_policies: int
    scaledown_status: dict


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok", "service": "CivicLens API"}


# ---------------------------------------------------------------------------
# Policies Feed
# ---------------------------------------------------------------------------

@router.get("/policies", response_model=List[PolicyResponse])
async def list_policies(
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    tag: Optional[str] = None,
    date_from: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return cached policy feed (no LLM calls here — instant response)."""
    from datetime import datetime as dt
    parsed_date_from = None
    if date_from:
        try:
            parsed_date_from = dt.fromisoformat(date_from)
        except ValueError:
            pass
    policies = get_policies(db, skip=skip, limit=limit, source=source, tag=tag, date_from=parsed_date_from)
    return [p.to_dict() for p in policies]


# ---------------------------------------------------------------------------
# Single Policy
# ---------------------------------------------------------------------------

@router.get("/policy/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """Return a single policy with full details."""
    policy = get_policy_by_id(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.to_dict()


# ---------------------------------------------------------------------------
# RAG Query
# ---------------------------------------------------------------------------

@router.post("/query", response_model=QueryResponse)
async def query_policies(request: QueryRequest, db: Session = Depends(get_db)):
    """
    RAG-based Q&A with ScaleDown optimization.
    Retrieves relevant policy chunks, compresses with ScaleDown, queries LLM.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = await answer_query(
        query=request.query,
        top_k=request.top_k,
        db=db,
    )
    return result


# ---------------------------------------------------------------------------
# Upload Bill / PDF
# ---------------------------------------------------------------------------

@router.post("/upload")
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or text file for indexing.
    Extraction, summarization, and embedding run in background.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_types = {
        "application/pdf",
        "text/plain",
        "text/html",
        "application/octet-stream",
    }
    content_type = file.content_type or "application/octet-stream"

    # Read file bytes
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Extract text
    try:
        if file.filename.lower().endswith(".pdf") or "pdf" in content_type:
            text = extract_pdf_text(data)
        else:
            text = data.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract text: {e}")

    text = clean_text(text)
    if len(text) < 50:
        raise HTTPException(status_code=422, detail="File content too short to process")

    doc_title = title or file.filename.replace(".pdf", "").replace("_", " ").title()
    policy_id = str(uuid.uuid4())

    # Quick DB insert (without summary yet)
    policy = Policy(
        id=policy_id,
        title=doc_title[:500],
        source="Upload",
        summary="Processing...",
        tags=[],
        key_clauses=[],
        link=f"upload://{policy_id}",
        raw_content=text[:50000],
        is_indexed=False,
    )
    db.add(policy)
    db.commit()

    # Background: summarize + classify + embed
    background_tasks.add_task(
        _process_uploaded_policy, policy_id, text, doc_title
    )

    return {
        "policy_id": policy_id,
        "title": doc_title,
        "status": "processing",
        "message": "Document uploaded. Summarization and indexing in progress.",
        "chars": len(text),
    }


async def _process_uploaded_policy(policy_id: str, text: str, title: str) -> None:
    """Background task: analyze, classify, and embed an uploaded document."""
    from ..db.database import db_session

    try:
        analysis = await analyze_policy(text, title)
        tags = await classify_policy(text, title)
        await _embed_and_store(policy_id, text, title, "Upload")

        with db_session() as db:
            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            if policy:
                policy.summary = analysis["summary"]
                policy.key_clauses = analysis["key_clauses"]
                policy.tags = tags
                policy.is_indexed = True

        logger.info(f"Upload processed: {title}")

    except Exception as e:
        logger.error(f"Upload processing failed for {policy_id}: {e}")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: Session = Depends(get_db)):
    """Return system metrics: policy counts, token savings, compression stats."""
    from ..optimization.scaledown_pipeline import get_optimizer

    stats = get_stats(db)
    optimizer = get_optimizer()

    scaledown_status = {
        "compressor_available": optimizer.compressor_available,
        "semantic_optimizer_available": optimizer.semantic_optimizer_available,
        "mode": (
            "ScaleDown API"
            if optimizer.compressor_available
            else "Local FAISS Fallback"
        ),
    }

    return {**stats, "scaledown_status": scaledown_status}


# ---------------------------------------------------------------------------
# Manual ingestion trigger (dev/admin)
# ---------------------------------------------------------------------------

@router.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger a policy ingestion run (for development/testing)."""
    background_tasks.add_task(run_ingestion)
    return {"status": "ingestion_started", "message": "Ingestion running in background"}


# ---------------------------------------------------------------------------
# Re-summarize policies missing summaries (admin)
# ---------------------------------------------------------------------------

@router.post("/admin/rescan")
async def rescan_summaries(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Re-run LLM analysis on all policies with missing or placeholder summaries."""
    missing = db.query(Policy).filter(
        (Policy.summary == None) |
        (Policy.summary == "Summary not available.") |
        (Policy.summary == "Processing...")
    ).all()

    count = len(missing)
    if count == 0:
        return {"status": "nothing_to_do", "count": 0}

    jobs = [(p.id, p.raw_content or "", p.title, p.source) for p in missing]
    background_tasks.add_task(_rescan_policies, jobs)

    return {"status": "rescan_started", "count": count, "message": f"Re-summarizing {count} policies in background"}


async def _rescan_policies(jobs: list) -> None:
    """Background task: re-analyze and re-embed policies with missing summaries."""
    from ..db.database import db_session
    import asyncio

    for policy_id, content, title, source in jobs:
        try:
            if not content or len(content) < 50:
                logger.warning(f"Skipping {title!r}: no raw content")
                continue

            analysis = await analyze_policy(content, title)
            tags = await classify_policy(content, title)

            with db_session() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    policy.summary = analysis["summary"]
                    policy.key_clauses = analysis["key_clauses"]
                    policy.tags = tags

            try:
                await _embed_and_store(policy_id, content, title, source or "Unknown")
                with db_session() as db:
                    policy = db.query(Policy).filter(Policy.id == policy_id).first()
                    if policy:
                        policy.is_indexed = True
            except Exception as embed_err:
                logger.warning(f"Embedding failed for {title!r} (summary saved): {embed_err}")

            logger.info(f"Rescan complete: {title[:60]}")
            await asyncio.sleep(1)  # avoid rate limiting

        except Exception as e:
            logger.error(f"Rescan failed for {title!r}: {e}")


# ---------------------------------------------------------------------------
# Re-embed all policies (admin) — use after changing embedding model
# ---------------------------------------------------------------------------

@router.post("/admin/reindex")
async def reindex_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Re-embed all policies into the vector store (run after changing embedding model)."""
    policies = db.query(Policy).filter(Policy.raw_content != None).all()
    jobs = [(p.id, p.raw_content or "", p.title, p.source or "Unknown") for p in policies
            if p.raw_content and len(p.raw_content) >= 50]
    count = len(jobs)
    background_tasks.add_task(_reindex_policies, jobs)
    return {"status": "reindex_started", "count": count, "message": f"Re-embedding {count} policies in background"}


async def _reindex_policies(jobs: list) -> None:
    """Background task: re-embed all policies with the current embedding model."""
    from ..db.database import db_session
    import asyncio

    for policy_id, content, title, source in jobs:
        try:
            await _embed_and_store(policy_id, content, title, source)
            with db_session() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    policy.is_indexed = True
            logger.info(f"Reindexed: {title[:60]}")
        except Exception as e:
            logger.warning(f"Reindex failed for {title!r}: {e}")
        await asyncio.sleep(0.1)
