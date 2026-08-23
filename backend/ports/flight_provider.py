from typing import Protocol

from schemas.flights import FlightOffer, FlightSearchRequest, FlightSearchReturnRequest, BookingOption


class FlightSearchError(Exception):
    """Raised when the flight provider fails to return usable results."""


class FlightProvider(Protocol):
    def search(self, request: FlightSearchRequest) -> list[FlightOffer]: ...
    def search_return(self, request: FlightSearchReturnRequest) -> list[FlightOffer]: ...
    def get_booking_options(self, offer: FlightOffer) -> list[BookingOption]: ...
