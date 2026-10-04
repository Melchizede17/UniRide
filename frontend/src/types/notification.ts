export interface AppNotification {
  id: string;
  type: string;
  message: string;
  is_read: boolean;
  related_ride_id: string | null;
  created_at: string;
}
