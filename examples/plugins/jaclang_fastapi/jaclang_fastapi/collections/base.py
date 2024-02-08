from os import getenv

from bson import ObjectId

from pydantic import BaseModel

from pymongo import IndexModel
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.server_api import ServerApi

from motor.motor_asyncio import AsyncIOMotorClient

from jaclang_fastapi.utils import logger


class BaseCollection:
    __collection__ = None
    __collection_obj__: Collection = None
    __indexes__ = []
    __excluded__ = []
    __excluded_obj__ = None

    __client__: AsyncIOMotorClient = None
    __database__: Database = None

    @classmethod
    def __document__(cls, doc: dict):
        return doc

    @classmethod
    def __documents__(cls, docs: list[dict]):
        return docs

    @staticmethod
    def get_client() -> AsyncIOMotorClient:
        if not isinstance(__class__.__client__, AsyncIOMotorClient):
            __class__.__client__ = AsyncIOMotorClient(
                getenv("DATABASE_HOST"),
                server_api=ServerApi("1"),
            )

        return __class__.__client__

    @staticmethod
    async def get_session() -> ClientSession:
        return await __class__.get_client().start_session()

    @staticmethod
    def get_database() -> Database:
        if not isinstance(__class__.__database__, Database):
            __class__.__database__ = __class__.get_client().get_database(
                getenv("DATABASE_NAME")
            )

        return __class__.__database__

    @staticmethod
    def get_collection(collection: str) -> Collection:
        return __class__.get_database().get_collection(collection)

    @classmethod
    async def collection(cls, session: ClientSession = None) -> Collection:
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
                await cls.__collection_obj__.create_indexes(idxs, session=session)

        return cls.__collection_obj__

    @classmethod
    async def insert_one(cls, doc: dict, session: ClientSession = None):
        try:
            collection = await cls.collection(session=session)
            result = await collection.insert_one(doc, session=session)
            return result.inserted_id
        except Exception:
            if session:
                raise
            logger.exception(f"Error inserting doc:\n{doc}")
        return []

    @classmethod
    async def insert_many(cls, docs: list[dict], session: ClientSession = None):
        try:
            collection = await cls.collection(session=session)
            result = await collection.insert_many(docs, session=session)
            return result.inserted_ids
        except Exception:
            if session:
                raise
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
    async def delete(cls, filter, session: ClientSession = None):
        try:
            collection = await cls.collection(session=session)
            result = await collection.delete_many(filter, session=session)
            return result.deleted_count
        except Exception:
            if session:
                raise
            logger.exception(f"Error delete with filter:\n{filter}")
        return 0

    @classmethod
    async def delete_one(cls, filter, session: ClientSession = None):
        try:
            collection = await cls.collection(session=session)
            result = await collection.delete_one(filter, session=session)
            return result.deleted_count
        except Exception:
            if session:
                raise
            logger.exception(f"Error delete one with filter:\n{filter}")
        return 0

    @classmethod
    async def delete_by_id(cls, id: str, session: ClientSession = None):
        try:
            collection = await cls.collection(session=session)
            result = await collection.delete_one({"_id": ObjectId(id)}, session=session)
            return result.deleted_count
        except Exception:
            if session:
                raise
            logger.exception(f"Error delete by id [{id}]")
        return 0
