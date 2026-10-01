import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (Index("idx_routes_route_geometry", "route_geometry", postgresql_using="gist"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ride_requests.id", ondelete="CASCADE"), unique=True
    )

    route_geometry: Mapped[str] = mapped_column(
        Geography(geometry_type="LINESTRING", srid=4326, spatial_index=False)
    )
    distance_meters: Mapped[float]
    duration_seconds: Mapped[int]
    provider: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    ride_request: Mapped["RideRequest"] = relationship(back_populates="route")  # noqa: F821
