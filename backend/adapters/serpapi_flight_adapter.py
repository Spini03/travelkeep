import html
import os
import re
import uuid
import requests
import serpapi
from datetime import datetime

from ports.flight_provider import FlightProvider, FlightSearchError, ResolveFailedError
from schemas.flights import FlightOffer, FlightSearchRequest, BookingOption, FlightLeg, Journey

TRAVEL_CLASS_TO_SERPAPI = {"economy": 1, "premium_economy": 2, "business": 3, "first": 4}
TRIP_TYPE_TO_SERPAPI = {"round_trip": 1, "one_way": 2, "multi_city": 3}
META_REFRESH_URL_PATTERN = re.compile(r"url=['\"]([^'\"]+)['\"]")


class SerpApiFlightAdapter:
    """Only file in the codebase allowed to import the serpapi SDK for flights."""

    def search(self, request: FlightSearchRequest) -> list[FlightOffer]:
        params = self._build_search_params(request)
        return self._run_search(params)

    def get_booking_options(self, offer: FlightOffer) -> list[BookingOption]:
        params = self._build_booking_options_params(offer)
        try:
            search = serpapi.search(params)
            data = search.data
        except Exception as e:
            raise FlightSearchError(f"SerpApi booking options request failed: {e}") from e

        booking_options_raw = data.get("booking_options", [])
        if not booking_options_raw:
            raise FlightSearchError("SerpApi returned no booking options")

        return [
            option
            for raw in booking_options_raw
            for option in self._map_booking_options_entry(raw)
        ]

    def _build_booking_options_params(self, offer: FlightOffer) -> dict:
        base = {
            "api_key": os.environ.get("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "en", "gl": "us",
            "currency": offer.currency,
            "booking_token": offer.booking_token,
        }

        if len(offer.journeys) <= 2:
            outbound_journey = offer.journeys[0]
            base["departure_id"] = outbound_journey.legs[0].departure_airport_code
            base["arrival_id"] = outbound_journey.legs[-1].arrival_airport_code
            base["outbound_date"] = outbound_journey.legs[0].departure_time.date().isoformat()
            if len(offer.journeys) > 1:
                return_journey = offer.journeys[1]
                base["return_date"] = return_journey.legs[0].departure_time.date().isoformat()
        else:
            # Hipótesis sin confirmar en doc de SerpApi (sin ejemplo de booking_token
            # para multi-city de 3+ tramos): mismo patrón que _build_search_params()
            # usa para multi_city — reflejar la estructura original de búsqueda.
            import json
            base["type"] = TRIP_TYPE_TO_SERPAPI["multi_city"]
            base["multi_city_json"] = json.dumps([
                {
                    "departure_id": journey.legs[0].departure_airport_code,
                    "arrival_id": journey.legs[-1].arrival_airport_code,
                    "date": journey.legs[0].departure_time.date().isoformat(),
                }
                for journey in offer.journeys
            ])

        return base

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

        if request.departure_token:
            base["departure_token"] = request.departure_token

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

    def _map_booking_options_entry(self, raw: dict) -> list[BookingOption]:
        together = raw.get("together")
        if together and (together.get("booking_request") or together.get("booking_phone")):
            return [self._map_seller_entry(together, is_partial_ticket=False)]

        # "together" sin link ni teléfono => tickets separados por tramo/vendedor.
        # SerpApi no documenta el nombre de estas claves (visto "flight_1".."flight_N"
        # para multi-city; la doc menciona "departing"/"returning" para round-trip de
        # 2 tramos) — se toma cualquier clave extra en vez de asumir un patrón fijo.
        sub_entries = {k: v for k, v in raw.items() if k not in ("separate_tickets", "together")}
        if sub_entries:
            return [self._map_seller_entry(entry, is_partial_ticket=True) for entry in sub_entries.values()]

        return [self._map_seller_entry(together, is_partial_ticket=False)] if together else []

    def _map_seller_entry(self, entry: dict, is_partial_ticket: bool) -> BookingOption:
        booking_request = entry.get("booking_request")
        baggage_prices = entry.get("baggage_prices")
        return BookingOption(
            seller_name=entry.get("book_with", ""),
            booking_link=booking_request.get("url") if booking_request else None,
            post_data=booking_request.get("post_data") if booking_request else None,
            price=float(entry.get("price", 0)),
            baggage_info="; ".join(baggage_prices) if baggage_prices else None,
            booking_phone=entry.get("booking_phone"),
            is_partial_ticket=is_partial_ticket,
        )

    def resolve_booking_link(self, booking_option: BookingOption) -> str:
        response = requests.post(
            booking_option.booking_link,
            data=booking_option.post_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
        )
        # Google's endpoint returns a client-side meta-refresh, not an HTTP redirect —
        # requests only follows 3xx/Location, so the seller's real URL has to be parsed
        # out of the HTML body instead of read off response.url.
        match = META_REFRESH_URL_PATTERN.search(response.text)
        if not match:
            raise ResolveFailedError(
                f"No se pudo extraer la URL de redirect del meta-refresh (status={response.status_code})"
            )
        redirect_url = html.unescape(match.group(1))

        try:
            final_response = requests.get(redirect_url, allow_redirects=True)
        except requests.RequestException as e:
            raise ResolveFailedError(f"Fallo al seguir el redirect a {redirect_url}: {e}") from e

        return final_response.url
