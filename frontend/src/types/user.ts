export interface User {
  id: string;
  email: string;
  display_name: string;
  university: string | null;
  gender: string | null;
  email_verified: boolean;
  created_at: string;
}

export type GenderPreference = "NO_PREFERENCE" | "PREFER_SAME_GENDER" | "REQUIRE_SAME_GENDER";

export interface UserPreferences {
  gender_preference: GenderPreference;
  default_time_window_minutes: number;
  default_pickup_radius_meters: number;
}

export interface Token {
  access_token: string;
  token_type: string;
}
