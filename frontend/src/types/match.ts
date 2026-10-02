import type { RideRequest } from "./ride";

export type MatchStatus = "SUGGESTED" | "A_ACCEPTED" | "B_ACCEPTED" | "CONFIRMED" | "REJECTED" | "EXPIRED" | "CANCELLED";

export interface Match {
  id: string;
  my_ride_id: string;
  other_ride: RideRequest;
  destination_score: number;
  time_score: number;
  pickup_score: number;
  preference_score: number;
  route_overlap_score: number;
  total_score: number;
  status: MatchStatus;
  accepted_by_me: boolean;
  accepted_by_other: boolean;
  created_at: string;
}
