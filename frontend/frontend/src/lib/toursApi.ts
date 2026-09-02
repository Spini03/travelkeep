import { apiRequest } from "@/lib/api";
import { TourSearchResponse } from "@/types/tour";

export async function searchTours(city: string) {
  return apiRequest<TourSearchResponse>(
    `/api/tours/search?city=${encodeURIComponent(city)}`,
    {
      method: "GET",
    }
  );
}
