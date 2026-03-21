"""SQLAlchemy database models for CivicLens."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, JSON, Boolean
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=_uuid)
    title = Column(String(500), nullable=False)
    source = Column(String(50), nullable=False)          # PRS | PIB | Gazette | Upload
    date = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(JSON, default=list)                    # ["citizens", "startups", ...]
    key_clauses = Column(JSON, default=list)             # ["clause1", "clause2", ...]
    link = Column(String(1000), nullable=True, unique=True)
    raw_content = Column(Text, nullable=True)
    is_indexed = Column(Boolean, default=False)          # True when embeddings stored
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "date": self.date.isoformat() if self.date else None,
            "summary": self.summary,
            "tags": self.tags or [],
            "key_clauses": self.key_clauses or [],
            "link": self.link,
            "is_indexed": self.is_indexed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    source_policy_ids = Column(JSON, default=list)
    original_tokens = Column(Integer, default=0)
    compressed_tokens = Column(Integer, default=0)
    compression_ratio = Column(Float, default=1.0)
    savings_percent = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    scaledown_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query_text": self.query_text,
            "answer_text": self.answer_text,
            "source_policy_ids": self.source_policy_ids or [],
            "original_tokens": self.original_tokens,
            "compressed_tokens": self.compressed_tokens,
            "compression_ratio": self.compression_ratio,
            "savings_percent": self.savings_percent,
            "latency_ms": self.latency_ms,
            "scaledown_used": self.scaledown_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
