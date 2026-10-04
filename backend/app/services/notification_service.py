import uuid

from sqlalchemy.orm import Session

from app.models import Notification
from app.schemas.notification import NotificationRead
from app.services.connection_manager import connection_manager


async def notify_user(
    db: Session,
    user_id: uuid.UUID,
    notification_type: str,
    message: str,
    related_ride_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        related_ride_id=related_ride_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    payload = NotificationRead.model_validate(notification).model_dump(mode="json")
    await connection_manager.send_to_user(user_id, {"event": "notification", "data": payload})

    return notification
