import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID as UUID_TYPE
from urllib.parse import urlparse

from models.accommodations import Accommodations
from models.scrape_cache import ScrapeCache
from schemas.accommodations import AccommodationCreate, AccommodationUpdate
from utils.scrapper import scrape_accommodation, ScrapeBlockedError

logger = logging.getLogger(__name__)

SCRAPE_CACHE_TTL = timedelta(days=7)


class AccommodationsService:
    """CRUD services for accommodations links"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AccommodationCreate) -> Accommodations:
        # Check for existing by unique key (itinerary_id, url)
        existing: Optional[Accommodations] = (
            self.db.query(Accommodations)
            .filter(
                and_(
                    Accommodations.itinerary_id == data.itinerary_id,
                    Accommodations.url == str(data.url),
                )
            )
            .first()
        )

        if existing is not None:
            if existing.status == "deleted":
                # Revive deleted entry as draft
                existing.status = "draft"
                self.db.commit()
                self.db.refresh(existing)
                return existing
            # Already present and active
            raise ValueError("This accommodation is already in the list for this itinerary")

        url_str = str(data.url)
        scraped_data, scrape_status, scrape_warning = self._get_scrape_data(url_str)
        provider = scraped_data["provider"]
        title = scraped_data["title"]
        description = scraped_data["description"]
        img_urls = scraped_data["images"]

        new_record = Accommodations(
            itinerary_id=data.itinerary_id,
            city=data.city,
            url=url_str,
            title=title,
            description=description,
            img_urls=img_urls,
            provider=provider,
            scrape_status=scrape_status,
        )
        self.db.add(new_record)
        self.db.commit()
        self.db.refresh(new_record)
        new_record.scrape_warning = scrape_warning
        return new_record

    def _get_scrape_data(self, url_str: str):
        """Cache-aside lookup for scrape_accommodation(). Returns (data, scrape_status, scrape_warning)."""
        cache_hit = self.db.query(ScrapeCache).filter(ScrapeCache.url == url_str).first()
        if cache_hit is not None:
            age = datetime.now(timezone.utc) - cache_hit.scraped_at
            if age < SCRAPE_CACHE_TTL:
                logger.info("Scrape cache hit for URL %s (age=%s)", url_str, age)
                return cache_hit.data, "success", None

        try:
            scraped_data = scrape_accommodation(url_str)
        except ScrapeBlockedError as e:
            logger.warning("Scrape blocked for accommodation URL %s: %s", url_str, e)
            fallback_data = {
                "provider": self._detect_provider(url_str),
                "title": None,
                "description": None,
                "images": [],
            }
            warning = "No se pudo obtener información automática de este link, completá los datos manualmente"
            return fallback_data, "blocked", warning
        except Exception as e:
            logger.warning("Scrape failed for accommodation URL %s: %s", url_str, e)
            fallback_data = {
                "provider": self._detect_provider(url_str),
                "title": None,
                "description": None,
                "images": [],
            }
            warning = "No se pudo obtener información automática de este link, completá los datos manualmente"
            return fallback_data, "error", warning

        if cache_hit is not None:
            cache_hit.data = scraped_data
            cache_hit.scraped_at = datetime.now(timezone.utc)
        else:
            self.db.add(ScrapeCache(url=url_str, data=scraped_data))
        self.db.commit()

        return scraped_data, "success", None

    def get_by_id(self, accommodation_id: UUID_TYPE) -> Optional[Accommodations]:
        return self.db.query(Accommodations).filter(Accommodations.id == accommodation_id).first()

    def list_by_itinerary_and_city(self, itinerary_id: UUID_TYPE, city: str, skip: int = 0, limit: int = 100) -> List[Accommodations]:
        return (
            self.db.query(Accommodations)
            .filter(and_(Accommodations.itinerary_id == itinerary_id, Accommodations.city == city))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_itinerary(self, itinerary_id: UUID_TYPE, skip: int = 0, limit: int = 100) -> List[Accommodations]:
        return (
            self.db.query(Accommodations)
            .filter(and_(Accommodations.itinerary_id == itinerary_id))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, accommodation_id: UUID_TYPE, data: AccommodationUpdate) -> Optional[Accommodations]:
        record = self.get_by_id(accommodation_id)
        if not record:
            return None
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "img_urls" and value is not None:
                value = [str(u) for u in value]
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def soft_delete(self, accommodation_id: UUID_TYPE) -> Optional[Accommodations]:
        record = self.get_by_id(accommodation_id)
        if not record:
            return None
        record.status = "deleted"
        self.db.commit()
        self.db.refresh(record)
        return record

    def hard_delete(self, accommodation_id: UUID_TYPE) -> bool:
        record = self.get_by_id(accommodation_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True

    def _detect_provider(self, url_str: str) -> str:
        """Return provider name based on URL host."""
        try:
            host = urlparse(url_str).netloc.lower()
        except Exception:
            return "OTHER"

        if "airbnb." in host:
            return "AIRBNB"
        if "booking." in host:
            return "BOOKING"
        if "expedia." in host:
            return "EXPEDIA"
        return "OTHER"

def get_accommodations_service(db: Session) -> AccommodationsService:
    return AccommodationsService(db)


