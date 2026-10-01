import type { RideRequest } from "../types/ride";

export function RideCard({
  ride,
  onCancel,
}: {
  ride: RideRequest;
  onCancel?: (rideId: string) => void;
}) {
  const canCancel = onCancel && (ride.status === "ACTIVE" || ride.status === "MATCH_PENDING");

  return (
    <article className="ride-card">
      <div className="ride-card-route">
        <strong>{ride.pickup_address}</strong>
        <span> → </span>
        <strong>{ride.destination_address}</strong>
      </div>
      <div className="ride-card-meta">
        <span>{new Date(ride.departure_time).toLocaleString()}</span>
        <span className={`status status-${ride.status.toLowerCase()}`}>{ride.status}</span>
        <span>
          {ride.passenger_count} passenger{ride.passenger_count > 1 ? "s" : ""}
        </span>
      </div>
      {canCancel && (
        <button type="button" onClick={() => onCancel(ride.id)}>
          Cancel
        </button>
      )}
    </article>
  );
}
