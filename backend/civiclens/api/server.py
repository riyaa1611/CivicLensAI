"""FastAPI application factory."""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings
from ..db.database import init_db
from ..ingestion.scheduler import start_scheduler, stop_scheduler
from .routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    logger.info("CivicLens API starting...")
    init_db()

    # Seed initial data in background so startup doesn't block the event loop
    asyncio.create_task(_seed_initial_data())

    # Start background scheduler
    start_scheduler()
    logger.info("CivicLens API ready ✓")

    yield

    # Shutdown
    stop_scheduler()
    logger.info("CivicLens API stopped")


async def _seed_initial_data() -> None:
    """Seed the database with initial policy data on first run."""
    from ..db.database import db_session
    from ..db.models import Policy
    from ..ingestion.scheduler import run_ingestion

    with db_session() as db:
        count = db.query(Policy).count()

    if count == 0:
        logger.info("Empty database — running initial ingestion...")
        await run_ingestion()


def create_app() -> FastAPI:
    app = FastAPI(
        title="CivicLens API",
        description=(
            "AI-powered civic intelligence platform — tracks government policies, "
            "summarizes them, and answers questions using RAG + ScaleDown optimization."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
