from jaclang.core.construct import (
    Architype,
    DSFunc,
    NodeArchitype as _NodeArchitype,
    EdgeArchitype as _EdgeArchitype,
    NodeAnchor,
    EdgeAnchor,
    EdgeDir,
    Root as _Root,
)

from bson import ObjectId

from pymongo.client_session import ClientSession

from dataclasses import field, dataclass, asdict
from typing import Type, Callable, Union, Optional
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from jaclang_fastapi.collections import BaseCollection
from jaclang_fastapi.utils import logger


@dataclass(eq=False)
class DocAnchor:
    type: str
    id: ObjectId = field(default_factory=ObjectId)
    update: Union[bool, list[str]] = field(default_factory=list)


class Root(_Root):

    def __init__(self, id: ObjectId, date_created: int) -> None:
        """Create node architype."""
        self.id = id
        self.date_created = date_created
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("root")

    class Collection(BaseCollection):
        __collection__ = f"root"

        @classmethod
        def __document__(cls, doc: dict):
            return Root(id=doc.pop("_id"), **doc)


class NodeArchitype(_NodeArchitype):
    """Node Architype Protocol."""

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("node", update=True)
        self.Collection: BaseCollection

    async def save(self, session: ClientSession = None):
        if session:
            if self._jac_doc_.update == True:
                self._jac_doc_.update = False
                edges = [None, [], [], []]  # can be used in future
                for edir, earchs in self._jac_.edges.items():
                    for earch in earchs:
                        edges[edir.value].append(await earch.save(session))

                await self.Collection.insert_one(
                    {"_id": self._jac_doc_.id, "edg": edges, "ctx": asdict(self)},
                    session=session,
                )
            elif self._jac_doc_.update:
                pass
        else:
            async with await BaseCollection.get_session() as session:
                async with session.start_transaction():
                    try:
                        await self.save(session)
                        await session.commit_transaction()
                    except Exception:
                        await session.abort_transaction()
                        logger.exception("Error saving node!")
                        raise

        return self._jac_doc_.id


class EdgeArchitype(_EdgeArchitype):
    """Edge Architype Protocol."""

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("edge", update=True)
        self.Collection: BaseCollection

    async def save(self, session: ClientSession = None):
        if session:
            if self._jac_doc_.update == True:
                self._jac_doc_.update = []

                await self.Collection.insert_one(
                    {
                        "_id": self._jac_doc_.id,
                        "src": await self._jac_.source.save(session),
                        "tgt": await self._jac_.target.save(session),
                        "dir": self._jac_.dir.value,
                        "ctx": asdict(self),
                    },
                    session=session,
                )
            elif self._jac_doc_.update:
                pass
        else:
            async with await BaseCollection.get_session() as session:
                async with session.start_transaction():
                    try:
                        await self.save(session)
                        await session.commit_transaction()
                    except Exception:
                        await session.abort_transaction()
                        logger.exception("Error saving edge!")
                        raise

        return self._jac_doc_.id


@dataclass
class GenericEdge(EdgeArchitype):

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("edge", update=True)

    class Collection(BaseCollection):
        __collection__ = f"e_generic"


class JacPlugin:
    @staticmethod
    @hookimpl
    def make_node(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a obj architype."""

        def decorator(cls: Type[Architype]) -> Type[Architype]:
            """Decorate class."""
            cls = Jac.make_architype(
                cls, arch_base=NodeArchitype, on_entry=on_entry, on_exit=on_exit
            )
            populate_collection(cls, "n")
            return cls

        return decorator

    @staticmethod
    @hookimpl
    def make_edge(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a edge architype."""

        def decorator(cls: Type[Architype]) -> Type[Architype]:
            """Decorate class."""
            cls = Jac.make_architype(
                cls, arch_base=EdgeArchitype, on_entry=on_entry, on_exit=on_exit
            )
            populate_collection(cls, "e")
            return cls

        return decorator

    @staticmethod
    @hookimpl
    def build_edge(
        edge_dir: EdgeDir,
        conn_type: Optional[Type[Architype]],
        conn_assign: Optional[tuple[tuple, tuple]],
    ) -> Architype:
        """Jac's root getter."""
        conn_type = conn_type if conn_type else GenericEdge
        edge = conn_type()
        if isinstance(edge._jac_, EdgeAnchor):
            edge._jac_.dir = edge_dir
        else:
            raise TypeError("Invalid edge object")
        if conn_assign:
            for fld, val in zip(conn_assign[0], conn_assign[1]):
                if hasattr(edge, fld):
                    setattr(edge, fld, val)
                else:
                    raise ValueError(f"Invalid attribute: {fld}")
        return edge


def populate_collection(cls: type, prefix: str) -> type:
    if (coll := getattr(cls, "Collection", None)) is None:

        class Collection(BaseCollection):
            __collection__ = f"{prefix[:1]}_{cls.__name__.lower()}"
            __excluded__ = []  # private fields
            __indexes__ = []  # not sure yet

        cls.Collection = Collection
    elif not issubclass(coll, BaseCollection):
        cls.Collection = type(coll.__name__, (coll, BaseCollection), {})

    return cls
