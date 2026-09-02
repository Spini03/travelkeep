from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from models.scrape_cache import ScrapeCache
from ports.tour_provider import TourProvider
from schemas.tours import TourResult, TourSearchResponse

TOUR_CACHE_TTL = timedelta(days=7)


class TourService:
    def __init__(self, db: Session, provider: TourProvider):
        self.db = db
        self._provider = provider

    def search(self, city: str) -> TourSearchResponse:
        cache_key = _cache_key(city)
        cache_hit = self.db.query(ScrapeCache).filter(ScrapeCache.url == cache_key).first()
        if cache_hit is not None:
            age = datetime.now(timezone.utc) - cache_hit.scraped_at
            if age < TOUR_CACHE_TTL:
                results = [TourResult(**data) for data in cache_hit.data["results"]]
                return self._build_response(city, results)

        results = self._scrape_and_cache(city, cache_key, cache_hit)
        return self._build_response(city, results)

    def retry(self, city: str) -> TourSearchResponse:
        cache_key = _cache_key(city)
        cache_hit = self.db.query(ScrapeCache).filter(ScrapeCache.url == cache_key).first()
        results = self._scrape_and_cache(city, cache_key, cache_hit)
        return self._build_response(city, results)

    def _build_response(self, city: str, results: list[TourResult]) -> TourSearchResponse:
        fallback_url = self._provider.get_fallback_search_url(city) if not results else None
        return TourSearchResponse(results=results, fallback_search_url=fallback_url)

    def _scrape_and_cache(self, city: str, cache_key: str, cache_hit: ScrapeCache | None) -> list[TourResult]:
        results = self._provider.search_tours(city)
        data = {"results": [result.model_dump() for result in results]}

        if cache_hit is not None:
            cache_hit.data = data
            cache_hit.scraped_at = datetime.now(timezone.utc)
        else:
            self.db.add(ScrapeCache(url=cache_key, data=data))
        self.db.commit()

        return results


def _cache_key(city: str) -> str:
    # Namespaced (not a real URL) so it never collides with the accommodation
    # scrape cache, and so future providers (Viator, GuruWalk) can coexist
    # under tours:<provider>:<city> without key collisions.
    return f"tours:getyourguide:{city.strip().lower()}"


def get_tours_service(db: Session) -> TourService:
    from adapters.getyourguide_adapter import GetYourGuideAdapter
    return TourService(db, GetYourGuideAdapter())
