import { Link } from "react-router-dom";
import { useNotifications } from "../hooks/useNotifications";

export function NotificationsPage() {
  const { notifications, markAsRead } = useNotifications();

  return (
    <section>
      <h1>Notifications</h1>
      {notifications.length === 0 && <p>No notifications yet.</p>}
      <div className="ride-list">
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`notification-card ${notification.is_read ? "" : "notification-unread"}`}
            onClick={() => !notification.is_read && markAsRead(notification.id)}
          >
            <p>{notification.message}</p>
            <div className="ride-card-meta">
              <span>{new Date(notification.created_at).toLocaleString()}</span>
              {notification.related_ride_id && (
                <Link to={`/rides/${notification.related_ride_id}/matches`} onClick={(e) => e.stopPropagation()}>
                  View matches
                </Link>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
