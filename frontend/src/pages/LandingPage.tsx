import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function LandingPage() {
  const { token, isLoading } = useAuth();

  if (isLoading) return null;
  if (token) return <Navigate to="/dashboard" replace />;

  return (
    <section className="landing">
      <h1>UniRide</h1>
      <p>Find compatible students to share a ride and split the cost.</p>
      <div className="landing-actions">
        <Link to="/login" className="button-link">
          Log in
        </Link>
        <Link to="/register" className="button-link">
          Register
        </Link>
      </div>
    </section>
  );
}
