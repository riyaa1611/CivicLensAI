"""
Embedding generation using BAAI/bge-small-en-v1.5 via sentence-transformers.
Dimension: 384
"""
import logging
from typing import List
import numpy as np

from ..config.settings import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            _model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}") from e
    return _model


def embed_text(text: str) -> List[float]:
    """
    Embed a single text string.
    Returns a list of floats (384-dimensional for BAAI/bge-small-en-v1.5).
    """
    model = _get_model()
    # BGE models benefit from prepending "Represent this sentence:"
    prefixed = f"Represent this sentence: {text}" if text else ""
    embedding = model.encode(prefixed, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Embed a batch of texts efficiently.
    Returns list of embedding vectors.
    """
    if not texts:
        return []

    model = _get_model()
    prefixed = [f"Represent this sentence: {t}" for t in texts]
    embeddings = model.encode(
        prefixed,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 50,
    )
    return [emb.tolist() for emb in embeddings]


def embed_query(query: str) -> List[float]:
    """
    Embed a search query (uses query-specific prefix for BGE models).
    """
    model = _get_model()
    prefixed = f"Represent this query for searching relevant passages: {query}"
    embedding = model.encode(prefixed, normalize_embeddings=True)
    return embedding.tolist()
