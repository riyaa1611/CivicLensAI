import os
import sys
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()

# Add ScaleDown root to sys.path so it can be imported as a library
_SCALEDOWN_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SCALEDOWN_ROOT not in sys.path:
    sys.path.insert(0, _SCALEDOWN_ROOT)


class Settings(BaseSettings):
    # Database (Defaults to SQLite for local development, override with NEON_URL in production)
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./civiclens.db")

    # OpenRouter / LLM
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Pinecone (optional, but recommended for cloud)
    pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "civiclens-policies")
    pinecone_index_host: Optional[str] = os.getenv("PINECONE_INDEX_HOST")

    # ScaleDown (optional)
    scaledown_api_key: Optional[str] = os.getenv("SCALEDOWN_API_KEY")

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Ingestion
    ingestion_interval_hours: int = int(os.getenv("INGESTION_INTERVAL_HOURS", "6"))

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://civiclens-ai-chi.vercel.app",
        "https://civiclens.vercel.app",  # Keeping old one just in case
    ]

    model_config = {
        "env_file": os.path.join(_SCALEDOWN_ROOT, ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
