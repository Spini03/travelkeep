from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.tours import TourSearchResponse
from services.tours import get_tours_service

tours_router = APIRouter(prefix="/api", tags=["tours"])


@tours_router.get("/tours/search")
def search_tours(city: Annotated[str, Query(min_length=1)], db: Session = Depends(get_db)) -> TourSearchResponse:
    service = get_tours_service(db)
    return service.search(city)


@tours_router.post("/tours/search/retry")
def retry_tours_search(city: Annotated[str, Query(min_length=1)], db: Session = Depends(get_db)) -> TourSearchResponse:
    service = get_tours_service(db)
    return service.retry(city)
