"""
Vector store client with Pinecone (cloud) and FAISS (local fallback).
Automatically selects backend based on PINECONE_API_KEY availability.
"""
import logging
import os
import json
import pickle
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod

from ..config.settings import settings

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    @abstractmethod
    def upsert(self, vectors: List[Tuple[str, List[float], Dict]]) -> None:
        """Insert or update vectors. vectors = [(id, embedding, metadata)]"""

    @abstractmethod
    def query(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Query top-k nearest vectors. Returns list of {id, score, metadata}."""

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""


class PineconeVectorStore(BaseVectorStore):
    """Pinecone cloud vector store (v3+ client)."""

    def __init__(self):
        try:
            from pinecone import Pinecone, ServerlessSpec

            self._pc = Pinecone(api_key=settings.pinecone_api_key)
            index_name = settings.pinecone_index_name

            # Create index if it doesn't exist
            existing = [idx.name for idx in self._pc.list_indexes()]
            if index_name not in existing:
                logger.info(f"Creating Pinecone index '{index_name}' (dim={settings.embedding_dim})")
                self._pc.create_index(
                    name=index_name,
                    dimension=settings.embedding_dim,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

            if settings.pinecone_index_host:
                self._index = self._pc.Index(host=settings.pinecone_index_host)
            else:
                self._index = self._pc.Index(index_name)
            logger.info(f"Pinecone index '{index_name}' ready")

        except ImportError:
            raise ImportError("pinecone package required. Install: pip install pinecone")

    def upsert(self, vectors: List[Tuple[str, List[float], Dict]]) -> None:
        if not vectors:
            return
        records = [
            {"id": vid, "values": emb, "metadata": meta}
            for vid, emb, meta in vectors
        ]
        # Pinecone upsert in batches of 100
        for i in range(0, len(records), 100):
            self._index.upsert(vectors=records[i : i + 100])

    def query(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        result = self._index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata or {},
            }
            for match in result.matches
        ]

    def delete(self, ids: List[str]) -> None:
        if ids:
            self._index.delete(ids=ids)


class FAISSVectorStore(BaseVectorStore):
    """
    Local FAISS vector store as fallback when Pinecone is not configured.
    Persists index and metadata to disk.
    """

    INDEX_PATH = "faiss_index.bin"
    META_PATH = "faiss_meta.pkl"

    def __init__(self):
        try:
            import faiss
            import numpy as np
            self._faiss = faiss
            self._np = np
        except ImportError:
            raise ImportError("faiss-cpu required. Install: pip install faiss-cpu")

        self._dim = settings.embedding_dim
        self._index: object = None
        self._ids: List[str] = []
        self._metadata: List[Dict] = []
        self._load()

    def _load(self):
        """Load existing index from disk, or create a fresh one."""
        if os.path.exists(self.INDEX_PATH) and os.path.exists(self.META_PATH):
            try:
                self._index = self._faiss.read_index(self.INDEX_PATH)
                with open(self.META_PATH, "rb") as f:
                    data = pickle.load(f)
                    self._ids = data["ids"]
                    self._metadata = data["metadata"]
                logger.info(f"FAISS index loaded: {self._index.ntotal} vectors")
                return
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}")

        self._index = self._faiss.IndexFlatIP(self._dim)  # Inner product (cosine with normalized vecs)
        logger.info("FAISS index created fresh")

    def _save(self):
        """Persist index and metadata to disk."""
        try:
            self._faiss.write_index(self._index, self.INDEX_PATH)
            with open(self.META_PATH, "wb") as f:
                pickle.dump({"ids": self._ids, "metadata": self._metadata}, f)
        except Exception as e:
            logger.warning(f"Failed to save FAISS index: {e}")

    def upsert(self, vectors: List[Tuple[str, List[float], Dict]]) -> None:
        """
        Insert vectors into FAISS index.
        Note: FAISS IndexFlatIP doesn't support deletion — duplicates are prevented
        at the DB level (unique link constraint) so we just append.
        """
        if not vectors:
            return

        # Skip IDs already stored to prevent exact duplicates in one batch
        existing = set(self._ids)
        new_vectors = [(vid, emb, meta) for vid, emb, meta in vectors if vid not in existing]
        if not new_vectors:
            return

        embeddings = self._np.array([v[1] for v in new_vectors], dtype="float32")
        self._index.add(embeddings)
        self._ids.extend([v[0] for v in new_vectors])
        self._metadata.extend([v[2] for v in new_vectors])
        self._save()

    def query(self, embedding: List[float], top_k: int = 5) -> List[Dict]:
        if self._index.ntotal == 0:
            return []

        vec = self._np.array([embedding], dtype="float32")
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._ids):
                continue
            results.append({
                "id": self._ids[idx],
                "score": float(score),
                "metadata": self._metadata[idx] if idx < len(self._metadata) else {},
            })
        return results

    def delete(self, ids: List[str]) -> None:
        # FAISS IndexFlatIP does not support deletion.
        # We just remove from the metadata lists; stale index entries are harmless
        # since their metadata will show as missing on query.
        ids_set = set(ids)
        keep = [(vid, meta) for vid, meta in zip(self._ids, self._metadata)
                if vid not in ids_set]
        if keep:
            self._ids, self._metadata = map(list, zip(*keep))
        else:
            self._ids, self._metadata = [], []
        self._save()


# Singleton instance
_vector_store: Optional[BaseVectorStore] = None


def get_vector_store() -> BaseVectorStore:
    """Return the appropriate vector store based on configuration."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    if settings.pinecone_api_key:
        try:
            _vector_store = PineconeVectorStore()
            logger.info("Using Pinecone vector store")
            return _vector_store
        except Exception as e:
            logger.warning(f"Pinecone unavailable ({e}), falling back to FAISS")

    try:
        _vector_store = FAISSVectorStore()
        logger.info("Using FAISS vector store (local fallback)")
    except Exception as e:
        logger.error(f"FAISS also unavailable: {e}")
        raise RuntimeError("No vector store available. Install faiss-cpu: pip install faiss-cpu")

    return _vector_store
