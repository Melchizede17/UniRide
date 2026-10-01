import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RideCard } from "../components/RideCard";
import { useAuth } from "../hooks/useAuth";
import { cancelRideRequest, listMyActiveRides } from "../services/api";
import type { RideRequest } from "../types/ride";

export function DashboardPage() {
  const { token, user } = useAuth();
  const [rides, setRides] = useState<RideRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    listMyActiveRides(token)
      .then(setRides)
      .catch(() => setError("Could not load your ride requests"))
      .finally(() => setIsLoading(false));
  }, [token]);

  async function handleCancel(rideId: string) {
    if (!token) return;
    await cancelRideRequest(token, rideId);
    setRides((current) => current.filter((ride) => ride.id !== rideId));
  }

  return (
    <section>
      <h1>Welcome, {user?.display_name}</h1>
      <Link to="/rides/new" className="button-link">
        + Find a Ride
      </Link>

      <h2>Your active ride requests</h2>
      {isLoading && <p>Loading…</p>}
      {error && <p className="form-error">{error}</p>}
      {!isLoading && rides.length === 0 && <p>No active ride requests yet.</p>}
      <div className="ride-list">
        {rides.map((ride) => (
          <RideCard key={ride.id} ride={ride} onCancel={handleCancel} />
        ))}
      </div>
    </section>
  );
}
