import type { Match } from "../types/match";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function MatchCard({
  match,
  onAccept,
  onReject,
  isUpdating,
}: {
  match: Match;
  onAccept: (matchId: string) => void;
  onReject: (matchId: string) => void;
  isUpdating: boolean;
}) {
  const { other_ride } = match;
  const isTerminal = match.status === "REJECTED" || match.status === "CANCELLED" || match.status === "EXPIRED";
  const isConfirmed = match.status === "CONFIRMED";

  return (
    <article className="match-card">
      <div className="match-card-header">
        <strong>{pct(match.total_score)} match</strong>
        <span className={`status status-${match.status.toLowerCase()}`}>{match.status}</span>
      </div>

      <div className="ride-card-route">
        <strong>{other_ride.pickup_address}</strong>
        <span> → </span>
        <strong>{other_ride.destination_address}</strong>
      </div>
      <div className="ride-card-meta">
        <span>{new Date(other_ride.departure_time).toLocaleString()}</span>
        <span>
          {other_ride.passenger_count} passenger{other_ride.passenger_count > 1 ? "s" : ""}
        </span>
      </div>

      <dl className="score-breakdown">
        <div>
          <dt>Destination</dt>
          <dd>{pct(match.destination_score)}</dd>
        </div>
        <div>
          <dt>Time</dt>
          <dd>{pct(match.time_score)}</dd>
        </div>
        <div>
          <dt>Pickup</dt>
          <dd>{pct(match.pickup_score)}</dd>
        </div>
        <div>
          <dt>Preference</dt>
          <dd>{pct(match.preference_score)}</dd>
        </div>
      </dl>

      {isConfirmed && <p className="match-status-note">Confirmed — coordinate your ride together.</p>}
      {!isConfirmed && !isTerminal && match.accepted_by_me && !match.accepted_by_other && (
        <p className="match-status-note">You accepted — waiting on the other rider.</p>
      )}

      {!isConfirmed && !isTerminal && (
        <div className="match-actions">
          {!match.accepted_by_me && (
            <button type="button" onClick={() => onAccept(match.id)} disabled={isUpdating}>
              Accept
            </button>
          )}
          <button type="button" onClick={() => onReject(match.id)} disabled={isUpdating}>
            Decline
          </button>
        </div>
      )}
    </article>
  );
}
