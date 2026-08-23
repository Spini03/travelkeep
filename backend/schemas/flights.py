from datetime import date, datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class FlightLeg(BaseModel):
    airline: str
    airline_logo: str | None = None
    flight_number: str
    departure_airport_code: str
    departure_time: datetime
    arrival_airport_code: str
    arrival_time: datetime
    duration_minutes: int
    travel_class: str
    legroom: str | None = None


class Journey(BaseModel):
    legs: list[FlightLeg]
    duration_minutes: int


class PassengerCount(BaseModel):
    adults: int = Field(default=1, ge=1)
    children: int = 0
    infants_in_seat: int = 0
    infants_on_lap: int = 0


class FlightOffer(BaseModel):
    id: str
    price: float
    currency: str
    journeys: list[Journey]
    booking_token: str
    departure_token: str | None = None


class BookingOption(BaseModel):
    seller_name: str
    booking_link: str
    price: float
    baggage_info: str | None = None


class SearchLeg(BaseModel):
    origin: str
    destination: str
    date: date


class FlightSearchRequest(BaseModel):
    trip_type: Literal["one_way", "round_trip", "multi_city"]
    legs: list[SearchLeg]
    return_date: date | None = None
    passengers: PassengerCount
    travel_class: Literal["economy", "premium_economy", "business", "first"] = "economy"

    @model_validator(mode="after")
    def validate_legs_for_trip_type(self):
        if self.trip_type == "round_trip":
            if len(self.legs) != 1 or self.return_date is None:
                raise ValueError("round_trip requiere 1 leg y return_date")
        elif self.trip_type == "one_way":
            if len(self.legs) != 1 or self.return_date is not None:
                raise ValueError("one_way requiere 1 leg y sin return_date")
        elif self.trip_type == "multi_city":
            if len(self.legs) < 2 or self.return_date is not None:
                raise ValueError("multi_city requiere 2+ legs y sin return_date")
        return self


class FlightSearchReturnRequest(BaseModel):
    departure_token: str
    origin: str
    destination: str
    outbound_date: date
    return_date: date
    passengers: PassengerCount
    travel_class: str = "economy"


class SaveFlightRequest(BaseModel):
    offer: FlightOffer
    passengers: PassengerCount


class FlightResponse(BaseModel):
    id: UUID
    itinerary_id: UUID
    price: float
    currency: str
    passengers: PassengerCount
    journeys: list[Journey]
    booking_options: list[BookingOption]
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True
