"""BaseCollection Interface."""

from os import getenv
from typing import Any, AsyncGenerator, Callable, Union

from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCursor

from pymongo import DeleteMany, DeleteOne, IndexModel, InsertOne, UpdateMany, UpdateOne
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.server_api import ServerApi

from ..utils import logger


class BaseCollection:
    """
    Base collection interface.

    This interface use for connecting to mongodb.
    """

    __collection__ = None
    __collection_obj__: Collection = None
    __indexes__ = []
    __excluded__ = []
    __excluded_obj__ = None

    __client__: AsyncIOMotorClient = None  # type: ignore
    __database__: Database = None

    @classmethod
    def __document__(cls, doc: dict) -> dict:
        """
        Return parsed version of document.

        This the default parser after getting a single document.
        You may override this to specify how/which class it will be casted/based.
        """
        return doc

    @classmethod
    async def __documents__(cls, docs: AsyncIOMotorCursor) -> AsyncGenerator[Any, None]:  # type: ignore
        """
        Return parsed version of multiple documents.

        This the default parser after getting a list of documents.
        You may override this to specify how/which class it will be casted/based.
        """
        return (cls.__document__(doc) async for doc in docs)

    @staticmethod
    def get_client() -> AsyncIOMotorClient:  # type: ignore
        """Return pymongo.database.Database for mongodb connection."""
        if not isinstance(__class__.__client__, AsyncIOMotorClient):
            __class__.__client__ = AsyncIOMotorClient(
                getenv(
                    "DATABASE_HOST",
                    "mongodb://localhost/?retryWrites=true&w=majority",
                ),
                server_api=ServerApi("1"),
            )

        return __class__.__client__

    @staticmethod
    async def get_session() -> ClientSession:
        """Return pymongo.client_session.ClientSession used for mongodb transactional operations."""
        return await __class__.get_client().start_session()

    @staticmethod
    def get_database() -> Database:
        """Return pymongo.database.Database for database connection based from current client connection."""
        if not isinstance(__class__.__database__, Database):
            __class__.__database__ = __class__.get_client().get_database(
                getenv("DATABASE_NAME", "jaclang")
            )

        return __class__.__database__

    @staticmethod
    def get_collection(collection: str) -> Collection:
        """Return pymongo.collection.Collection for collection connection based from current database connection."""
        return __class__.get_database().get_collection(collection)

    @classmethod
    async def collection(cls, session: ClientSession = None) -> Collection:
        """Return pymongo.collection.Collection for collection connection based from attribute of it's child class."""
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
    async def insert_one(cls, doc: dict, session: ClientSession = None) -> ObjectId:
        """Insert single document and return the inserted id."""
        try:
            collection = await cls.collection(session=session)
            result = await collection.insert_one(doc, session=session)
            return result.inserted_id
        except Exception:
            if session:
                raise
            logger.exception(f"Error inserting doc:\n{doc}")
        return None

    @classmethod
    async def insert_many(
        cls, docs: list[dict], session: ClientSession = None
    ) -> list[ObjectId]:
        """Insert multiple documents and return the inserted ids."""
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
    async def update_one(
        cls, filter: dict, update: dict, session: ClientSession = None
    ) -> int:
        """Update single document and return if it's modified or not."""
        try:
            collection = await cls.collection(session=session)
            result = await collection.update_one(filter, update, session=session)
            return result.modified_count
        except Exception:
            if session:
                raise
            logger.exception(f"Error updating doc:\n{filter}\n{update}")
        return 0

    @classmethod
    async def update_many(
        cls, filter: dict, update: dict, session: ClientSession = None
    ) -> int:
        """Update multiple documents and return how many docs are modified."""
        try:
            collection = await cls.collection(session=session)
            result = await collection.update_many(filter, update, session=session)
            return result.modified_count
        except Exception:
            if session:
                raise
            logger.exception(f"Error updating doc:\n{filter}\n{update}")
        return 0

    @classmethod
    async def update_by_id(
        cls, id: Union[str, ObjectId], update: dict, session: ClientSession = None
    ) -> int:
        """Update single document via ID and return if it's modified or not."""
        return await cls.update_one({"_id": ObjectId(id)}, update, session)

    @classmethod
    async def find(
        cls,
        *args: list[Any],
        cursor: Callable = lambda x: x,
        **kwargs: dict[str, Any],
    ) -> list[object]:
        """Retrieve multiple documents."""
        collection = await cls.collection()

        if "projection" not in kwargs:
            kwargs["projection"] = cls.__excluded_obj__

        docs = cursor(collection.find(*args, **kwargs))
        return await cls.__documents__(docs)

    @classmethod
    async def find_one(cls, *args: list[Any], **kwargs: dict[str, Any]) -> object:
        """Retrieve single document from db."""
        collection = await cls.collection()

        if "projection" not in kwargs:
            kwargs["projection"] = cls.__excluded_obj__

        if result := await collection.find_one(*args, **kwargs):
            return cls.__document__(result)
        return result

    @classmethod
    async def find_by_id(
        cls, id: Union[str, ObjectId], *args: list[Any], **kwargs: dict[str, Any]
    ) -> object:
        """Retrieve single document via ID."""
        return await cls.find_one({"_id": ObjectId(id)}, *args, **kwargs)

    @classmethod
    async def delete(cls, filter: dict, session: ClientSession = None) -> int:
        """Delete document/s via filter and return how many documents are deleted."""
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
    async def delete_one(cls, filter: dict, session: ClientSession = None) -> int:
        """Delete single document via filter and return if it's deleted or not."""
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
    async def delete_by_id(
        cls, id: Union[str, ObjectId], session: ClientSession = None
    ) -> int:
        """Delete single document via ID and return if it's deleted or not."""
        return await cls.delete_one({"_id": ObjectId(id)}, session)

    @classmethod
    async def bulk_write(
        cls,
        ops: list[Union[InsertOne, DeleteMany, DeleteOne, UpdateMany, UpdateOne]],
        session: ClientSession = None,
    ) -> dict:  # noqa ANN401
        """Bulk write operations."""
        try:
            collection = await cls.collection(session=session)
            result = await collection.bulk_write(ops, session=session)
            return result.bulk_api_result
        except Exception:
            if session:
                raise
            logger.exception(f"Error bulk write:\n{ops}")
        return {}
