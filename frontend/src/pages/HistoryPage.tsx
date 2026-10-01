import { useEffect, useState } from "react";
import { RideCard } from "../components/RideCard";
import { useAuth } from "../hooks/useAuth";
import { listMyRideHistory } from "../services/api";
import type { RideRequest } from "../types/ride";

export function HistoryPage() {
  const { token } = useAuth();
  const [rides, setRides] = useState<RideRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    listMyRideHistory(token)
      .then(setRides)
      .finally(() => setIsLoading(false));
  }, [token]);

  return (
    <section>
      <h1>Ride History</h1>
      {isLoading && <p>Loading…</p>}
      {!isLoading && rides.length === 0 && <p>No ride requests yet.</p>}
      <div className="ride-list">
        {rides.map((ride) => (
          <RideCard key={ride.id} ride={ride} />
        ))}
      </div>
    </section>
  );
}
