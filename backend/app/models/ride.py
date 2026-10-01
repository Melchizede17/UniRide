import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Enum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RideStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MATCH_PENDING = "MATCH_PENDING"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    COMPLETED = "COMPLETED"


class RideRequest(Base):
    __tablename__ = "ride_requests"
    __table_args__ = (
        Index("idx_ride_requests_pickup_point", "pickup_point", postgresql_using="gist"),
        Index("idx_ride_requests_destination_point", "destination_point", postgresql_using="gist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    pickup_address: Mapped[str]
    pickup_point: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=False))

    destination_address: Mapped[str]
    destination_point: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    departure_time: Mapped[datetime]
    time_flexibility_minutes: Mapped[int] = mapped_column(default=20)
    passenger_count: Mapped[int] = mapped_column(default=1)
    status: Mapped[RideStatus] = mapped_column(Enum(RideStatus, name="ride_status"), default=RideStatus.ACTIVE, index=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[datetime | None]

    user: Mapped["User"] = relationship(back_populates="ride_requests")  # noqa: F821
    route: Mapped["Route"] = relationship(back_populates="ride_request", uselist=False, cascade="all, delete-orphan")  # noqa: F821
