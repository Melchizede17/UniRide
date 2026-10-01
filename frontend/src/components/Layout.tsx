import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div>
      <header className="app-header">
        <Link to="/" className="brand">
          UniRide
        </Link>
        {user && (
          <nav className="app-nav">
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/rides/new">Find a Ride</Link>
            <Link to="/history">History</Link>
            <span className="user-name">{user.display_name}</span>
            <button type="button" onClick={handleLogout}>
              Log out
            </button>
          </nav>
        )}
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
