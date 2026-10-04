import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { getWebSocketUrl, listNotifications, markNotificationRead } from "../services/api";
import type { AppNotification } from "../types/notification";
import { useAuth } from "./useAuth";

interface NotificationsContextValue {
  notifications: AppNotification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  toasts: AppNotification[];
  dismissToast: (id: string) => void;
}

const NotificationsContext = createContext<NotificationsContextValue | undefined>(undefined);

const RECONNECT_DELAY_MS = 3000;

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [toasts, setToasts] = useState<AppNotification[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!token) {
      setNotifications([]);
      return;
    }
    listNotifications(token).then(setNotifications).catch(() => {});
  }, [token]);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    function connect() {
      if (cancelled) return;
      const socket = new WebSocket(getWebSocketUrl(token!));
      socketRef.current = socket;

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.event === "notification") {
            const notification = payload.data as AppNotification;
            setNotifications((current) => [notification, ...current]);
            setToasts((current) => [...current, notification]);
          }
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = () => {
        if (!cancelled) {
          reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      socketRef.current?.close();
    };
  }, [token]);

  function markAsRead(id: string) {
    if (!token) return;
    setNotifications((current) => current.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    markNotificationRead(token, id).catch(() => {});
  }

  function dismissToast(id: string) {
    setToasts((current) => current.filter((t) => t.id !== id));
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <NotificationsContext.Provider value={{ notifications, unreadCount, markAsRead, toasts, dismissToast }}>
      {children}
    </NotificationsContext.Provider>
  );
}

export function useNotifications(): NotificationsContextValue {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error("useNotifications must be used within a NotificationsProvider");
  }
  return context;
}
