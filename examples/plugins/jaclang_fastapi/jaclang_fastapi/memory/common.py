from os import getenv

from orjson import dumps, loads

from redis import Redis, asyncio as aioredis

from jaclang_fastapi.utils import logger


class CommonMemory:
    __table__ = "common"

    __redis__: Redis = None

    @staticmethod
    def get_rd() -> Redis:
        if not isinstance(__class__.__redis__, Redis):
            __class__.__redis__ = aioredis.from_url(getenv("REDIS_HOST"))

        return __class__.__redis__

    @classmethod
    async def get(cls, key: str):
        try:
            redis = cls.get_rd()
            return loads(await redis.get(key))
        except Exception:
            logger.exception(f"Error getting key {key}")
            return None

    @classmethod
    async def keys(cls):
        try:
            redis = cls.get_rd()
            return await redis.keys()
        except Exception:
            logger.exception("Error getting keys")
            return None

    @classmethod
    async def set(cls, key: str, data: dict):
        try:
            redis = cls.get_rd()
            return bool(await redis.set(key, dumps(data)))
        except Exception:
            logger.exception(f"Error setting key {key} with data\n{data}")
            return False

    @classmethod
    async def delete(cls, key: str):
        try:
            redis = cls.get_rd()
            return bool(await redis.delete(key))
        except Exception:
            logger.exception(f"Error deleting key {key}")
            return False

    @classmethod
    async def hget(cls, key: str):
        try:
            redis = cls.get_rd()
            return loads(await redis.hget(cls.__table__, key))
        except Exception:
            logger.exception(f"Error getting key {key} from {cls.__table__}")
            return None

    @classmethod
    async def hkeys(cls):
        try:
            redis = cls.get_rd()
            return await redis.hkeys(cls.__table__)
        except Exception:
            logger.exception(f"Error getting keys from {cls.__table__}")
            return None

    @classmethod
    async def hset(cls, key: str, data: dict):
        try:
            redis = cls.get_rd()
            return bool(await redis.hset(cls.__table__, key, dumps(data)))
        except Exception:
            logger.exception(
                f"Error setting key {key} from {cls.__table__} with data\n{data}"
            )
            return False

    @classmethod
    async def hdelete(cls, key: str):
        try:
            redis = cls.get_rd()
            return bool(await redis.hdel(cls.__table__, key))
        except Exception:
            logger.exception(f"Error deleting key {key} from {cls.__table__}")
            return False
