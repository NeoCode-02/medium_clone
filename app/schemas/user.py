from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    bio: str | None = None
    avatar: str | None = None


class UserCreate(UserBase):
    hashed_password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: str | None = Field(None, max_length=50)
    bio: str | None = None
    avatar: str | None = None


class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
