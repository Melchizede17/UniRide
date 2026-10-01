import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MatchStatus(str, enum.Enum):
    SUGGESTED = "SUGGESTED"
    A_ACCEPTED = "A_ACCEPTED"
    B_ACCEPTED = "B_ACCEPTED"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ride_requests.id", ondelete="CASCADE"), index=True)
    request_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ride_requests.id", ondelete="CASCADE"), index=True)

    destination_score: Mapped[float]
    time_score: Mapped[float]
    pickup_score: Mapped[float]
    preference_score: Mapped[float]
    route_overlap_score: Mapped[float]
    total_score: Mapped[float]

    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus, name="match_status"), default=MatchStatus.SUGGESTED, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    request_a: Mapped["RideRequest"] = relationship(foreign_keys=[request_a_id])  # noqa: F821
    request_b: Mapped["RideRequest"] = relationship(foreign_keys=[request_b_id])  # noqa: F821
    feedback: Mapped[list["MatchFeedback"]] = relationship(back_populates="match", cascade="all, delete-orphan")


class MatchFeedback(Base):
    __tablename__ = "match_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    accepted: Mapped[bool]
    reason: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    match: Mapped["Match"] = relationship(back_populates="feedback")
