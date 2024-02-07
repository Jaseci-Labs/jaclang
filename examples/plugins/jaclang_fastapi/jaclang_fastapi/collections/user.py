from .base import BaseCollection


class UserCollection(BaseCollection):
    __collection__ = "user"
    __excluded__ = ["password"]
    __indexes__ = [{"fields": ["email"], "unique": True}]

    @classmethod
    async def find_by_email(cls, email: str):
        return await cls.find_one(filter={"email": email}, projection=None)
