from os import getenv

from bson import ObjectId

from pydantic import BaseModel

from pymongo import IndexModel
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.server_api import ServerApi

from motor.motor_asyncio import AsyncIOMotorClient

from jaclang_fastapi.utils import logger


class BaseCollector:
    __collection__ = None
    __collection_obj__: Collection = None
    __indexes__ = []
    __excluded__ = []
    __excluded_obj__ = None

    __database__: Database = None

    @classmethod
    def __document__(cls, doc: dict):
        return doc

    @classmethod
    def __documents__(cls, docs: list[dict]):
        return docs

    @staticmethod
    def get_database() -> Database:
        if not isinstance(__class__.__database__, Database):
            __class__.__database__ = AsyncIOMotorClient(
                getenv("DATABASE_HOST"),
                server_api=ServerApi("1"),
            ).get_database("DATABASE_NAME")

        return __class__.__database__

    @staticmethod
    def get_collection(collection: str) -> Collection:
        return __class__.get_database().get_collection(collection)

    @classmethod
    async def collection(cls) -> Collection:
        if not isinstance(cls.__collection_obj__, Collection):
            cls.__collection_obj__ = cls.get_collection(
                getattr(cls, "__collection__", None) or cls.__name__.lower()
            )

            if cls.__excluded__:
                excl_obj = {}
                for excl in cls.__excluded__:
                    excl_obj[excl] = False
                cls.__excluded_obj__ = excl_obj

            if cls.__indexes__:
                idxs = []
                while cls.__indexes__:
                    idx = cls.__indexes__.pop()
                    idxs.append(IndexModel(idx.pop("fields"), **idx))
                await cls.__collection_obj__.create_indexes(idxs)

        return cls.__collection_obj__

    @classmethod
    async def insert_one(cls, doc: BaseModel):
        try:
            doc = dict(doc)
            collection = await cls.collection()
            result = await collection.insert_one(doc)
            return result.inserted_id
        except Exception:
            logger.exception(f"Error inserting doc:\n{doc}")
        return []

    @classmethod
    async def insert_many(cls, docs: list[BaseModel]):
        try:
            docs = [dict(doc) for doc in docs]
            collection = await cls.collection()
            result = await collection.insert_many()
            return result.inserted_ids
        except Exception:
            logger.exception(f"Error inserting docs:\n{docs}")
        return []

    @classmethod
    async def find(cls, **kwargs):
        collection = await cls.collection()

        if "projection" not in kwargs:
            kwargs["projection"] = cls.__excluded_obj__

        if results := await collection.find(**kwargs):
            return cls.__documents__(results)
        return results

    @classmethod
    async def find_one(cls, **kwargs):
        collection = await cls.collection()

        if "projection" not in kwargs:
            kwargs["projection"] = cls.__excluded_obj__

        if result := await collection.find_one(**kwargs):
            return cls.__document__(result)
        return result

    @classmethod
    async def find_by_id(cls, id: str, **kwargs):
        collection = await cls.collection()

        if "projection" not in kwargs:
            kwargs["projection"] = cls.__excluded_obj__

        if result := await collection.find_one({"_id": ObjectId(id)}, **kwargs):
            return cls.__document__(result)
        return result

    @classmethod
    async def delete(cls, filter):
        collection = await cls.collection()
        result = await collection.delete_many(filter)
        return result.deleted_count

    @classmethod
    async def delete_one(cls, filter):
        collection = await cls.collection()
        result = await collection.delete_one(filter)
        return result.deleted_count

    @classmethod
    async def delete_by_id(cls, id: str):
        collection = await cls.collection()
        result = await collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count


__all__ = ["BaseCollector"]
