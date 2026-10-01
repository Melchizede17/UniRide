import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import GenderPreference


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str
    university: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    university: str | None = None
    gender: str | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr
    display_name: str
    university: str | None
    gender: str | None
    email_verified: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPreferenceRead(BaseModel):
    model_config = {"from_attributes": True}

    gender_preference: GenderPreference
    default_time_window_minutes: int
    default_pickup_radius_meters: int


class UserPreferenceUpdate(BaseModel):
    gender_preference: GenderPreference | None = None
    default_time_window_minutes: int | None = Field(default=None, ge=0)
    default_pickup_radius_meters: int | None = Field(default=None, ge=0)
