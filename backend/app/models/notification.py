import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[str]
    message: Mapped[str]
    is_read: Mapped[bool] = mapped_column(default=False)
    # Not in the architecture doc's section 8.7 schema; added so the frontend
    # can deep-link a notification to the ride it's about. SET NULL on delete
    # so a historic notification survives the ride being removed.
    related_ride_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ride_requests.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notifications")  # noqa: F821
