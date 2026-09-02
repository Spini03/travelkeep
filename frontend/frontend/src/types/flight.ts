export interface PassengerCount {
  adults: number;
  children: number;
  infants_in_seat: number;
  infants_on_lap: number;
}

export interface SearchLeg {
  origin: string;
  destination: string;
  date: string;
}

export interface FlightSearchRequest {
  trip_type: "one_way" | "round_trip" | "multi_city";
  legs: SearchLeg[];
  return_date?: string | null;
  passengers: PassengerCount;
  travel_class?: "economy" | "premium_economy" | "business" | "first";
  departure_token?: string | null;
}

export interface FlightLeg {
  airline: string;
  airline_logo?: string | null;
  flight_number: string;
  departure_airport_code: string;
  departure_time: string;
  arrival_airport_code: string;
  arrival_time: string;
  duration_minutes: number;
  travel_class: string;
  legroom?: string | null;
}

export interface Journey {
  legs: FlightLeg[];
  duration_minutes: number;
}

export interface FlightOffer {
  id: string;
  price: number;
  currency: string;
  journeys: Journey[];
  booking_token: string;
  departure_token?: string | null;
}

export interface BookingOption {
  seller_name: string;
  booking_link?: string | null;
  post_data?: string | null;
  price: number;
  baggage_info?: string | null;
  booking_phone?: string | null;
  is_partial_ticket: boolean;
}

export interface SaveFlightRequest {
  offer: FlightOffer;
  passengers: PassengerCount;
}

export interface FlightResponse {
  id: string;
  itinerary_id: string;
  price: number;
  currency: string;
  passengers: PassengerCount;
  journeys: Journey[];
  booking_options: BookingOption[];
  provider: string;
  created_at: string;
}

export interface ResolveBookingOptionResponse {
  resolved_url?: string | null;
  seller_name: string;
  price: number;
  booking_phone?: string | null;
}
