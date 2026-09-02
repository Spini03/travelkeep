from pydantic import BaseModel


class TourResult(BaseModel):
    title: str
    price: float
    currency: str
    rating: float | None = None
    review_count: int | None = None
    image_url: str | None = None
    external_url: str
    category: str | None = None
    duration: str | None = None


class TourSearchResponse(BaseModel):
    results: list[TourResult]
    fallback_search_url: str | None = None
