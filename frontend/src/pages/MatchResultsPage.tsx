import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { MatchCard } from "../components/MatchCard";
import { useAuth } from "../hooks/useAuth";
import { acceptMatch, ApiError, getRideMatches, rejectMatch } from "../services/api";
import type { Match } from "../types/match";

export function MatchResultsPage() {
  const { rideId } = useParams<{ rideId: string }>();
  const { token } = useAuth();
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingMatchId, setUpdatingMatchId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMatches = useCallback(() => {
    if (!token || !rideId) return;
    setIsLoading(true);
    setError(null);
    getRideMatches(token, rideId)
      .then(setMatches)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load matches"))
      .finally(() => setIsLoading(false));
  }, [token, rideId]);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  async function handleAccept(matchId: string) {
    if (!token) return;
    setUpdatingMatchId(matchId);
    try {
      const updated = await acceptMatch(token, matchId);
      setMatches((current) => current.map((m) => (m.id === matchId ? updated : m)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not accept match");
    } finally {
      setUpdatingMatchId(null);
    }
  }

  async function handleReject(matchId: string) {
    if (!token) return;
    setUpdatingMatchId(matchId);
    try {
      const updated = await rejectMatch(token, matchId);
      setMatches((current) => current.map((m) => (m.id === matchId ? updated : m)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not decline match");
    } finally {
      setUpdatingMatchId(null);
    }
  }

  return (
    <section>
      <Link to="/dashboard">← Back to dashboard</Link>
      <h1>Matches</h1>
      <button type="button" onClick={loadMatches} disabled={isLoading}>
        {isLoading ? "Searching…" : "Refresh matches"}
      </button>

      {error && <p className="form-error">{error}</p>}
      {!isLoading && matches.length === 0 && !error && (
        <p>No compatible riders found yet. Try adjusting your ride details or check back later.</p>
      )}

      <div className="ride-list">
        {matches.map((match) => (
          <MatchCard
            key={match.id}
            match={match}
            onAccept={handleAccept}
            onReject={handleReject}
            isUpdating={updatingMatchId === match.id}
          />
        ))}
      </div>
    </section>
  );
}
