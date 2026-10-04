import { useEffect } from "react";
import { useNotifications } from "../hooks/useNotifications";

const AUTO_DISMISS_MS = 6000;

export function ToastContainer() {
  const { toasts, dismissToast } = useNotifications();

  useEffect(() => {
    const timers = toasts.map((toast) => setTimeout(() => dismissToast(toast.id), AUTO_DISMISS_MS));
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismissToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className="toast">
          <span>{toast.message}</span>
          <button type="button" onClick={() => dismissToast(toast.id)} aria-label="Dismiss">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
