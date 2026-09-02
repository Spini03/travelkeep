import { apiRequest } from "@/lib/api";
import {
  FlightSearchRequest,
  FlightOffer,
  SaveFlightRequest,
  FlightResponse,
  ResolveBookingOptionResponse,
} from "@/types/flight";

export async function searchFlights(request: FlightSearchRequest) {
  return apiRequest<FlightOffer[]>("/api/flights/search", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function saveFlight(
  itineraryId: string,
  request: SaveFlightRequest
) {
  return apiRequest<FlightResponse>(
    `/api/itineraries/${itineraryId}/flights`,
    {
      method: "POST",
      body: JSON.stringify(request),
    }
  );
}

export async function resolveBookingOption(
  flightId: string,
  sellerName: string
) {
  return apiRequest<ResolveBookingOptionResponse>(
    `/api/flights/${flightId}/booking-options/resolve`,
    {
      method: "POST",
      body: JSON.stringify({ seller_name: sellerName }),
    }
  );
}
