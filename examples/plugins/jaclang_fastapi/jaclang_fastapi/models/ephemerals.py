from pydantic import BaseModel, EmailStr

from jaclang_fastapi.securities import hashpw


class UserRequest(BaseModel):
    email: EmailStr
    password: str

    def parsed(self):
        return {"email": self.email, "password": hashpw(self.password)}
