import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GenderPreference(str, enum.Enum):
    NO_PREFERENCE = "NO_PREFERENCE"
    PREFER_SAME_GENDER = "PREFER_SAME_GENDER"
    REQUIRE_SAME_GENDER = "REQUIRE_SAME_GENDER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]
    display_name: Mapped[str]
    university: Mapped[str | None]
    email_verified: Mapped[bool] = mapped_column(default=False)
    gender: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    preferences: Mapped["UserPreference"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    ride_requests: Mapped[list["RideRequest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    gender_preference: Mapped[GenderPreference] = mapped_column(
        Enum(GenderPreference, name="gender_preference"), default=GenderPreference.NO_PREFERENCE
    )
    default_time_window_minutes: Mapped[int] = mapped_column(default=20)
    default_pickup_radius_meters: Mapped[int] = mapped_column(default=2000)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="preferences")
