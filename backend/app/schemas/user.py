from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    is_email_verified: bool
    created_at: datetime
    telegram_id: int | None = None
    telegram_username: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None

