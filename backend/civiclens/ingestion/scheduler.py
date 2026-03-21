"""APScheduler-based ingestion scheduler."""
import logging
import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config.settings import settings

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


async def run_ingestion() -> None:
    """Full ingestion pipeline: scrape → process → store → embed."""
    logger.info("Starting scheduled ingestion run...")
    try:
        # Import here to avoid circular imports
        from .prs_scraper import scrape_prs
        from .pib_scraper import scrape_pib
        from .gazette_scraper import scrape_gazette
        from .news_scraper import scrape_economic_times, scrape_business_today
        from .gov_schemes_scraper import scrape_gov_schemes
        from ..services.policy_service import ingest_policies

        prs_data = scrape_prs()
        pib_data = scrape_pib()
        gazette_data = scrape_gazette()
        et_data = scrape_economic_times()
        bt_data = scrape_business_today()
        schemes_data = scrape_gov_schemes()

        all_policies = prs_data + pib_data + gazette_data + et_data + bt_data + schemes_data
        logger.info(f"Scraped {len(all_policies)} policies total")

        await ingest_policies(all_policies)
        logger.info("Ingestion run completed")

    except Exception as e:
        logger.error(f"Ingestion run failed: {e}", exc_info=True)


def start_scheduler() -> AsyncIOScheduler:
    """Start the APScheduler with the ingestion job."""
    scheduler = get_scheduler()

    scheduler.add_job(
        run_ingestion,
        trigger=IntervalTrigger(hours=settings.ingestion_interval_hours),
        id="ingestion_job",
        name="Policy Ingestion",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started — ingestion every {settings.ingestion_interval_hours} hours"
    )
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
