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
from jaclang_fastapi.utils import utc_now, logger


@dataclass(eq=False)
class DocAnchor:
    name: str
    type: str
    id: ObjectId = field(default_factory=ObjectId)
    date_created: int = field(default_factory=utc_now)
    date_updated: int = field(default=None)
    connected: bool = field(default=False)
    upsert: Union[bool, list[str]] = field(default_factory=list)

    def init(
        self,
        id: ObjectId,
        n: str,
        t: str,
        dc: int,
        du: int,
        connected: bool = True,
        upsert: Union[bool, list[str]] = None,
    ):
        self.id = id
        self.name = n
        self.type = t
        self.date_created = dc
        self.date_updated = du
        self.connected = connected
        if upsert != None:
            self.upsert = upsert

    def up(self):
        self.date_updated = utc_now()

    def json(self):
        return {
            "_id": self.id,
            "_jd": {
                "dc": self.date_created,
                "du": self.date_created,
                "t": self.type,
                "n": self.name,
            },
        }


class NodeArchitype(_NodeArchitype):
    """Node Architype Protocol."""

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor(
            self.__class__.__name__, "node", upsert=True
        )
        self.Collection: BaseCollection

    def gen_edges(self, edges: list):

        for idx, edges in enumerate(edges):
            self._jac_.edges[EdgeDir(idx)].append()

    @classmethod
    async def one(cls, doc: dict):
        ret = cls(**doc.get("ctx"))
        for idx, edges in enumerate(doc.get("edg")):
            for edge in ret._jac_.edges:
                pass

    async def save(self, session: ClientSession = None):
        if session:
            if self._jac_doc_.upsert == True:
                self._jac_doc_.upsert = False
                edges = [[], [], [], []]  # can be used in future
                for edir, earchs in self._jac_.edges.items():
                    for earch in earchs:
                        edges[edir.value].append(await earch.save(session))

                await self.Collection.insert_one(
                    {**self._jac_doc_.json(), "edg": edges, "ctx": asdict(self)},
                    session=session,
                )
            elif self._jac_doc_.upsert:
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


@dataclass
class Root(NodeArchitype, _Root):
    _jac_entry_funcs_: list = field(default_factory=list)
    _jac_exit_funcs_: list = field(default_factory=list)

    def __post_init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor(
            self.__class__.__name__, "root", upsert=True
        )

    class Collection(BaseCollection):
        __collection__ = f"root"

        @classmethod
        def __document__(cls, doc: dict):
            root = Root()
            root._jac_doc_.init(id=doc.pop("_id"), **doc.pop("_jd"), upsert=[])
            root._jac_.edges
            return root


class EdgeArchitype(_EdgeArchitype):
    """Edge Architype Protocol."""

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor(
            self.__class__.__name__, "edge", upsert=True
        )
        self.Collection: BaseCollection

    async def save(self, session: ClientSession = None):
        if session:
            if self._jac_doc_.upsert == True:
                self._jac_doc_.upsert = []

                await self.Collection.insert_one(
                    {
                        **self._jac_doc_.json(),
                        "src": await self._jac_.source.save(session),
                        "tgt": await self._jac_.target.save(session),
                        "dir": self._jac_.dir.value,
                        "ctx": asdict(self),
                    },
                    session=session,
                )
            elif self._jac_doc_.upsert:
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
        self._jac_doc_: DocAnchor = DocAnchor(
            self.__class__.__name__, "edge", upsert=True
        )

    class Collection(BaseCollection):
        __collection__ = f"e"


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
