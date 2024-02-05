from pydantic import BaseModel, EmailStr

from jaclang_fastapi.collector import BaseCollector


class User(BaseModel):
    id: str
    email: EmailStr
    password: bytes

    def json(self):
        return {"id": self.id, "email": self.email}

    class Collector(BaseCollector):
        __collection__ = "user"
        __excluded__ = ["password"]
        __indexes__ = [{"fields": ["email"], "unique": True}]

        @classmethod
        def __document__(cls, doc) -> "User":
            return User(
                id=str(doc.get("_id")),
                email=doc.get("email"),
                password=doc.get("password"),
            )

        @classmethod
        def __documents__(cls, doc) -> "User":
            return User(
                id=str(doc.get("_id")),
                email=doc.get("email"),
                password=doc.get("password"),
            )

        @classmethod
        async def find_by_email(cls, email: str) -> "User":
            return await cls.find_one(filter={"email": email}, projection=None)
