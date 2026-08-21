"""Background job that periodically purges expired scrape_cache rows."""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from database import SessionLocal
from models.scrape_cache import ScrapeCache
from services.accommodations import SCRAPE_CACHE_TTL

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_HOURS = 24

scheduler = BackgroundScheduler()


def cleanup_expired_scrape_cache() -> int:
    """Delete scrape_cache rows older than SCRAPE_CACHE_TTL. Returns rows deleted."""
    cutoff = datetime.now(timezone.utc) - SCRAPE_CACHE_TTL
    db = SessionLocal()
    try:
        deleted = db.query(ScrapeCache).filter(ScrapeCache.scraped_at < cutoff).delete(synchronize_session=False)
        db.commit()
        logger.info("Scrape cache cleanup removed %d expired row(s)", deleted)
        return deleted
    finally:
        db.close()


def start_scrape_cache_scheduler() -> None:
    scheduler.add_job(
        cleanup_expired_scrape_cache,
        "interval",
        hours=CLEANUP_INTERVAL_HOURS,
        id="scrape_cache_cleanup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scrape cache cleanup scheduler started (every %dh)", CLEANUP_INTERVAL_HOURS)


def stop_scrape_cache_scheduler() -> None:
    scheduler.shutdown(wait=False)
