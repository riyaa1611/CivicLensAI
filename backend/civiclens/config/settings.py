"""CivicLens application settings."""
import os
import sys
from typing import List, Optional
from pydantic_settings import BaseSettings

# Add ScaleDown root to sys.path so it can be imported as a library
_SCALEDOWN_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SCALEDOWN_ROOT not in sys.path:
    sys.path.insert(0, _SCALEDOWN_ROOT)


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./civiclens.db"

    # OpenRouter / LLM
    openrouter_api_key: str = "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"
    llm_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Pinecone (optional)
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "civiclens-policies"
    pinecone_index_host: Optional[str] = None

    # ScaleDown (optional)
    scaledown_api_key: Optional[str] = None

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Ingestion
    ingestion_interval_hours: int = 6

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    model_config = {
        "env_file": os.path.join(_SCALEDOWN_ROOT, ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
