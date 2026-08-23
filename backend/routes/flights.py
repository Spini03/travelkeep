import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.flights import (
    FlightSearchRequest, FlightSearchReturnRequest, SaveFlightRequest,
    FlightOffer, FlightResponse,
)
from services.flights import get_flights_service
from ports.flight_provider import FlightSearchError

flights_router = APIRouter(prefix="/api", tags=["flights"])


@flights_router.post("/flights/search")
def search_flights(request: FlightSearchRequest, db: Session = Depends(get_db)) -> list[FlightOffer]:
    service = get_flights_service(db)
    try:
        return service.search(request)
    except FlightSearchError as e:
        raise HTTPException(status_code=502, detail=str(e))


@flights_router.post("/flights/search-return")
def search_return_flights(request: FlightSearchReturnRequest, db: Session = Depends(get_db)) -> list[FlightOffer]:
    service = get_flights_service(db)
    try:
        return service.search_return(request)
    except FlightSearchError as e:
        raise HTTPException(status_code=502, detail=str(e))


@flights_router.post("/itineraries/{itinerary_id}/flights", status_code=201)
def save_flight(itinerary_id: uuid.UUID, request: SaveFlightRequest, db: Session = Depends(get_db)) -> FlightResponse:
    service = get_flights_service(db)
    try:
        return service.save_flight(itinerary_id, request)
    except FlightSearchError as e:
        raise HTTPException(status_code=502, detail=str(e))


@flights_router.get("/itineraries/{itinerary_id}/flights")
def list_flights(itinerary_id: uuid.UUID, db: Session = Depends(get_db)) -> list[FlightResponse]:
    service = get_flights_service(db)
    return service.list_by_itinerary(itinerary_id)


@flights_router.get("/flights/{flight_id}")
def get_flight(flight_id: uuid.UUID, db: Session = Depends(get_db)) -> FlightResponse:
    service = get_flights_service(db)
    flight = service.get_by_id(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight


@flights_router.delete("/flights/{flight_id}", status_code=204)
def delete_flight(flight_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    service = get_flights_service(db)
    if not service.delete(flight_id):
        raise HTTPException(status_code=404, detail="Flight not found")
