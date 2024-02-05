from pydantic import BaseModel, EmailStr


class UserRequest(BaseModel):
    email: EmailStr
    password: str
