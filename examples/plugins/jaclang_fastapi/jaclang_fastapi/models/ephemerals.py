"""Ephemeral Models."""

from pydantic import BaseModel, EmailStr


class UserRequest(BaseModel):
    """User Creation Request Model."""

    email: EmailStr
    password: str
