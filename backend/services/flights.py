import uuid
from sqlalchemy.orm import Session
from models.flights import Flight
from schemas.flights import (
    FlightSearchRequest, FlightSearchReturnRequest, SaveFlightRequest,
    FlightOffer, Journey, ResolveBookingOptionResponse,
)
from ports.flight_provider import FlightProvider, SellerNotAvailableError


class FlightService:
    def __init__(self, db: Session, provider: FlightProvider):
        self.db = db
        self._provider = provider

    def search(self, request: FlightSearchRequest) -> list[FlightOffer]:
        return self._provider.search(request)

    def search_return(self, request: FlightSearchReturnRequest) -> list[FlightOffer]:
        return self._provider.search_return(request)

    def save_flight(self, itinerary_id: uuid.UUID, request: SaveFlightRequest) -> Flight:
        booking_options = self._provider.get_booking_options(request.offer)
        db_flight = Flight(
            itinerary_id=itinerary_id,
            price=request.offer.price,
            currency=request.offer.currency,
            passengers=request.passengers.model_dump(),
            journeys=[journey.model_dump(mode="json") for journey in request.offer.journeys],
            booking_options=[option.model_dump(exclude={"post_data"}) for option in booking_options],
            booking_token=request.offer.booking_token,
        )
        self.db.add(db_flight)
        self.db.commit()
        self.db.refresh(db_flight)
        return db_flight

    def resolve_booking_option(self, flight_id: uuid.UUID, seller_name: str) -> ResolveBookingOptionResponse | None:
        db_flight = self.get_by_id(flight_id)
        if not db_flight:
            return None

        offer = FlightOffer(
            id=str(db_flight.id),
            price=db_flight.price,
            currency=db_flight.currency,
            journeys=[Journey(**journey) for journey in db_flight.journeys],
            booking_token=db_flight.booking_token,
        )
        booking_options = self._provider.get_booking_options(offer)

        matched = next(
            (option for option in booking_options if option.seller_name.lower() == seller_name.lower()),
            None,
        )
        if not matched:
            raise SellerNotAvailableError(f"Seller '{seller_name}' no disponible, precios pueden haber cambiado")

        resolved_url = None
        if matched.post_data:
            resolved_url = self._provider.resolve_booking_link(matched)

        return ResolveBookingOptionResponse(
            resolved_url=resolved_url,
            seller_name=matched.seller_name,
            price=matched.price,
            booking_phone=matched.booking_phone,
        )

    def list_by_itinerary(self, itinerary_id: uuid.UUID) -> list[Flight]:
        return self.db.query(Flight).filter(Flight.itinerary_id == itinerary_id).all()

    def get_by_id(self, flight_id: uuid.UUID) -> Flight | None:
        return self.db.query(Flight).filter(Flight.id == flight_id).first()

    def delete(self, flight_id: uuid.UUID) -> bool:
        db_flight = self.get_by_id(flight_id)
        if not db_flight:
            return False
        self.db.delete(db_flight)
        self.db.commit()
        return True


def get_flights_service(db: Session) -> FlightService:
    from adapters.serpapi_flight_adapter import SerpApiFlightAdapter
    return FlightService(db, SerpApiFlightAdapter())
