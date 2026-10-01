export interface Coordinates {
  latitude: number;
  longitude: number;
}

export type RideStatus = "ACTIVE" | "MATCH_PENDING" | "MATCHED" | "CANCELLED" | "EXPIRED" | "COMPLETED";

export interface RideRequest {
  id: string;
  user_id: string;
  pickup_address: string;
  pickup: Coordinates;
  destination_address: string;
  destination: Coordinates;
  departure_time: string;
  time_flexibility_minutes: number;
  passenger_count: number;
  status: RideStatus;
  created_at: string;
  expires_at: string | null;
}

export interface RideRequestInput {
  pickup_address: string;
  pickup: Coordinates;
  destination_address: string;
  destination: Coordinates;
  departure_time: string;
  time_flexibility_minutes: number;
  passenger_count: number;
}
