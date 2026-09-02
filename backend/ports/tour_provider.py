from typing import Protocol

from schemas.tours import TourResult


class TourSearchError(Exception):
    """Raised when the tour provider fails to return usable results."""


class TourProvider(Protocol):
    def search_tours(self, city: str) -> list[TourResult]: ...
    def get_fallback_search_url(self, city: str) -> str | None: ...
