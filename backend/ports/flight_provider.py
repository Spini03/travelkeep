from typing import Protocol

from schemas.flights import FlightOffer, FlightSearchRequest, BookingOption


class FlightSearchError(Exception):
    """Raised when the flight provider fails to return usable results."""


class SellerNotAvailableError(Exception):
    """Raised when a previously seen seller no longer appears in fresh booking options."""


class ResolveFailedError(Exception):
    """Raised when the seller's redirect page can't be resolved to a final booking URL."""


class FlightProvider(Protocol):
    def search(self, request: FlightSearchRequest) -> list[FlightOffer]: ...
    def get_booking_options(self, offer: FlightOffer) -> list[BookingOption]: ...
    def resolve_booking_link(self, booking_option: BookingOption) -> str: ...
