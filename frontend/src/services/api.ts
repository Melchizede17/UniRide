import type { Match } from "../types/match";
import type { AppNotification } from "../types/notification";
import type { RideRequest, RideRequestInput } from "../types/ride";
import type { Token, User, UserPreferences } from "../types/user";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    throw new ApiError(response.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function checkHealth(): Promise<{ status: string }> {
  return request("/health");
}

export function registerUser(payload: {
  email: string;
  password: string;
  display_name: string;
  university?: string;
}): Promise<User> {
  return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
}

export function loginUser(payload: { email: string; password: string }): Promise<Token> {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}

export function getCurrentUser(token: string): Promise<User> {
  return request("/auth/me", {}, token);
}

export function getMyPreferences(token: string): Promise<UserPreferences> {
  return request("/users/me/preferences", {}, token);
}

export function updateMyPreferences(
  token: string,
  payload: Partial<UserPreferences>
): Promise<UserPreferences> {
  return request("/users/me/preferences", { method: "PATCH", body: JSON.stringify(payload) }, token);
}

export function createRideRequest(token: string, payload: RideRequestInput): Promise<RideRequest> {
  return request("/rides", { method: "POST", body: JSON.stringify(payload) }, token);
}

export function listMyActiveRides(token: string): Promise<RideRequest[]> {
  return request("/rides/me", {}, token);
}

export function listMyRideHistory(token: string): Promise<RideRequest[]> {
  return request("/rides/history", {}, token);
}

export function getRideRequest(token: string, rideId: string): Promise<RideRequest> {
  return request(`/rides/${rideId}`, {}, token);
}

export function cancelRideRequest(token: string, rideId: string): Promise<void> {
  return request(`/rides/${rideId}`, { method: "DELETE" }, token);
}

export function getRideMatches(token: string, rideId: string): Promise<Match[]> {
  return request(`/rides/${rideId}/matches`, {}, token);
}

export function acceptMatch(token: string, matchId: string): Promise<Match> {
  return request(`/matches/${matchId}/accept`, { method: "POST" }, token);
}

export function rejectMatch(token: string, matchId: string): Promise<Match> {
  return request(`/matches/${matchId}/reject`, { method: "POST" }, token);
}

export function listNotifications(token: string): Promise<AppNotification[]> {
  return request("/notifications", {}, token);
}

export function markNotificationRead(token: string, notificationId: string): Promise<AppNotification> {
  return request(`/notifications/${notificationId}/read`, { method: "PATCH" }, token);
}

export function getWebSocketUrl(token: string): string {
  const wsBase = API_BASE_URL.replace(/^http/, "ws");
  return `${wsBase}/ws/matches?token=${encodeURIComponent(token)}`;
}

export { ApiError };
