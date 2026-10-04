import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    type: str
    message: str
    is_read: bool
    related_ride_id: uuid.UUID | None
    created_at: datetime
