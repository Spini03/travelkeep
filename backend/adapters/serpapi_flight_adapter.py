import os
import uuid
import serpapi
from datetime import datetime

from ports.flight_provider import FlightProvider, FlightSearchError
from schemas.flights import (
    FlightOffer, FlightSearchRequest, FlightSearchReturnRequest,
    BookingOption, FlightLeg, Journey,
)

TRAVEL_CLASS_TO_SERPAPI = {"economy": 1, "premium_economy": 2, "business": 3, "first": 4}
TRIP_TYPE_TO_SERPAPI = {"round_trip": 1, "one_way": 2, "multi_city": 3}


class SerpApiFlightAdapter:
    """Only file in the codebase allowed to import the serpapi SDK for flights."""

    def search(self, request: FlightSearchRequest) -> list[FlightOffer]:
        params = self._build_search_params(request)
        return self._run_search(params)

    def search_return(self, request: FlightSearchReturnRequest) -> list[FlightOffer]:
        params = {
            "api_key": os.environ.get("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "en", "gl": "us",
            "type": TRIP_TYPE_TO_SERPAPI["round_trip"],
            "departure_id": request.origin,
            "arrival_id": request.destination,
            "outbound_date": request.outbound_date.isoformat(),
            "return_date": request.return_date.isoformat(),
            "departure_token": request.departure_token,
            "currency": "USD",
            "travel_class": TRAVEL_CLASS_TO_SERPAPI.get(request.travel_class, 1),
            "adults": request.passengers.adults,
            "children": request.passengers.children,
            "infants_in_seat": request.passengers.infants_in_seat,
            "infants_on_lap": request.passengers.infants_on_lap,
        }
        return self._run_search(params)

    def get_booking_options(self, offer: FlightOffer) -> list[BookingOption]:
        outbound_journey = offer.journeys[0]
        params = {
            "api_key": os.environ.get("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "en", "gl": "us",
            "currency": offer.currency,
            "booking_token": offer.booking_token,
            "departure_id": outbound_journey.legs[0].departure_airport_code,
            "arrival_id": outbound_journey.legs[-1].arrival_airport_code,
            "outbound_date": outbound_journey.legs[0].departure_time.date().isoformat(),
        }
        # Assumes exactly 2 journeys (round trip) when a return leg is present.
        # Doesn't generalize to 3+ multi-city legs — see multi-city backlog note in AGENTS.md.
        if len(offer.journeys) > 1:
            return_journey = offer.journeys[1]
            params["return_date"] = return_journey.legs[0].departure_time.date().isoformat()
        try:
            search = serpapi.search(params)
            data = search.data
        except Exception as e:
            raise FlightSearchError(f"SerpApi booking options request failed: {e}") from e

        booking_options_raw = data.get("booking_options", [])
        if not booking_options_raw:
            raise FlightSearchError("SerpApi returned no booking options")

        return [self._map_booking_option(raw) for raw in booking_options_raw]

    def _build_search_params(self, request: FlightSearchRequest) -> dict:
        base = {
            "api_key": os.environ.get("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "en", "gl": "us",
            "currency": "USD",
            "travel_class": TRAVEL_CLASS_TO_SERPAPI.get(request.travel_class, 1),
            "adults": request.passengers.adults,
            "children": request.passengers.children,
            "infants_in_seat": request.passengers.infants_in_seat,
            "infants_on_lap": request.passengers.infants_on_lap,
            "type": TRIP_TYPE_TO_SERPAPI[request.trip_type],
        }

        if request.trip_type == "multi_city":
            import json
            base["multi_city_json"] = json.dumps([
                {"departure_id": leg.origin, "arrival_id": leg.destination, "date": leg.date.isoformat()}
                for leg in request.legs
            ])
        else:
            leg = request.legs[0]
            base["departure_id"] = leg.origin
            base["arrival_id"] = leg.destination
            base["outbound_date"] = leg.date.isoformat()
            if request.trip_type == "round_trip":
                base["return_date"] = request.return_date.isoformat()

        return base

    def _run_search(self, params: dict) -> list[FlightOffer]:
        try:
            search = serpapi.search(params)
            data = search.data
        except Exception as e:
            raise FlightSearchError(f"SerpApi flight search failed: {e}") from e

        raw_offers = (data.get("best_flights") or []) + (data.get("other_flights") or [])
        if not raw_offers:
            raise FlightSearchError("SerpApi returned no flight offers")

        return [self._map_offer(raw) for raw in raw_offers]

    def _map_offer(self, raw: dict) -> FlightOffer:
        flights = raw.get("flights", [])
        legs = [self._map_leg(f) for f in flights]
        journey = Journey(legs=legs, duration_minutes=raw.get("total_duration", 0))
        return FlightOffer(
            id=str(uuid.uuid4()),
            price=float(raw.get("price", 0)),
            currency="USD",
            journeys=[journey],
            booking_token=raw.get("booking_token", ""),
            departure_token=raw.get("departure_token"),
        )

    def _map_leg(self, flight: dict) -> FlightLeg:
        departure_airport = flight.get("departure_airport", {})
        arrival_airport = flight.get("arrival_airport", {})
        return FlightLeg(
            airline=flight.get("airline", ""),
            airline_logo=flight.get("airline_logo"),
            flight_number=flight.get("flight_number", ""),
            departure_airport_code=departure_airport.get("id", ""),
            departure_time=datetime.fromisoformat(departure_airport.get("time", "")),
            arrival_airport_code=arrival_airport.get("id", ""),
            arrival_time=datetime.fromisoformat(arrival_airport.get("time", "")),
            duration_minutes=flight.get("duration", 0),
            travel_class=flight.get("travel_class", ""),
            legroom=flight.get("legroom"),
        )

    def _map_booking_option(self, raw: dict) -> BookingOption:
        together = raw.get("together", raw)
        book_with = together.get("book_with", "")
        price = together.get("price", 0)
        baggage_prices = together.get("baggage_prices")
        return BookingOption(
            seller_name=book_with,
            booking_link=together.get("booking_request", {}).get("url", "") or together.get("marketing_carrier", ""),
            price=float(price),
            baggage_info="; ".join(baggage_prices) if baggage_prices else None,
        )
