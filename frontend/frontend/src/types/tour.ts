export interface TourResult {
  title: string;
  price: number;
  currency: string;
  rating: number | null;
  review_count: number | null;
  image_url: string | null;
  external_url: string;
  category: string | null; // "tour" | "actividad" | "entrada" | null
  duration: string | null;
}

export type TourSearchStatus = "idle" | "loading" | "loaded" | "empty" | "error";

export interface TourSearchResponse {
  results: TourResult[];
  fallback_search_url: string | null;
}
