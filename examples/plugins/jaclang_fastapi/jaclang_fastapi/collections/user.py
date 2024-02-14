"""UserCollection Interface."""

from .base import BaseCollection


class UserCollection(BaseCollection):
    """
    User collection interface.

    This interface is for User's Management.
    You may override this if you wish to implement different structure
    """

    __collection__ = "user"
    __excluded__ = ["password"]
    __indexes__ = [{"fields": ["email"], "unique": True}]

    @classmethod
    async def find_by_email(cls, email: str) -> object:
        """Retrieve user via email."""
        return await cls.find_one(filter={"email": email}, projection=None)
