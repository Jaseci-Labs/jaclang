"""Common Classes for FastAPI Graph Integration."""

from contextvars import ContextVar
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from re import IGNORECASE, compile
from typing import Any, Callable, ClassVar, Optional, Union

from bson import ObjectId

from fastapi import Request

from jaclang.core.construct import (
    Architype,
    EdgeAnchor as _EdgeAnchor,
    EdgeArchitype as _EdgeArchitype,
    EdgeDir,
    NodeAnchor as _NodeAnchor,
    NodeArchitype as _NodeArchitype,
    Root as _Root,
    root as base_root,
)

from pymongo.client_session import ClientSession

from ..collections import BaseCollection
from ..utils import logger


TARGET_NODE_REGEX = compile(r"^([^:]+):(r|n|e):([a-f\d]{24})$", IGNORECASE)
JCONTEXT = ContextVar("JCONTEXT")


class JType(Enum):
    """Enum For Graph Types."""

    ROOT = 0
    NODE = 1
    EDGE = 2

    def __str__(self) -> str:
        """Return equivalent shorthand name."""
        return JTYPE[self.value]


JTYPE = ["r", "n", "e"]
JTYPE_DICT = {"r": JType.ROOT, "n": JType.NODE, "e": JType.EDGE}


class ArchCollection(BaseCollection):
    """Default Collection for Architypes."""

    @classmethod
    def build_node(cls, doc_anc: "DocAnchor", doc: dict) -> "NodeArchitype":
        """Translate EdgeArchitypes edges into DocAnchor edges."""
        arch: NodeArchitype = doc_anc.build(**(doc.get("context") or {}))
        arch._jac_.edges = [DocAnchor.ref(edge) for edge in (doc.get("edge") or [])]
        return arch

    @classmethod
    def build_edge(cls, doc_anc: "DocAnchor", doc: dict) -> "EdgeArchitype":
        """Build EdgeArchitypes from document."""
        arch: EdgeArchitype = doc_anc.build(**(doc.get("context") or {}))
        if src := doc.get("source"):
            arch._jac_.source = DocAnchor.ref(src)

        if tgt := doc.get("target"):
            arch._jac_.target = DocAnchor.ref(tgt)

        arch._jac_.is_undirected = doc.get("is_undirected")

        return arch

    @classmethod
    def get_model(cls, default: str) -> str:
        """Return Outter Model Class."""
        qual = cls.__qualname__.split(f".{cls.__name__}")
        if len(qual) > 1:
            return qual[0].split(".")[-1]
        return default


@dataclass
class DocAccess:
    """DocAnchor for Access Handler."""

    all: bool = False
    nodes: set[ObjectId] = field(default_factory=set)
    roots: set[ObjectId] = field(default_factory=set)

    def json(self) -> dict:
        """Return in dictionary type."""
        return {"all": self.all, "nodes": list(self.nodes), "roots": list(self.roots)}


@dataclass
class DocAnchor:
    """DocAnchor for Mongodb Referencing."""

    type: JType
    name: str
    id: ObjectId = field(default_factory=ObjectId)
    root: Optional["Root"] = None
    access: DocAccess = field(default_factory=DocAccess)
    connected: bool = False
    arch: Union["NodeArchitype", "EdgeArchitype", "Root", "GenericEdge"] = None
    changes: Optional[dict] = field(default_factory=dict)

    @property
    def ref_id(self) -> str:
        """Return id in reference type."""
        return f"{self.name}:{self.type}:{self.id}"

    @property
    def _set(self) -> dict:
        if "$set" not in self.changes:
            self.changes["$set"] = {}

        return self.changes.get("$set")

    @property
    def _pull(self) -> dict:
        if "$pull" not in self.changes:
            self.changes["$pull"] = {}

        return self.changes.get("$pull")

    @property
    def _push(self) -> dict:
        if "$push" not in self.changes:
            self.changes["$push"] = {}

        return self.changes.get("$push")

    def _edge(self, ops: dict, up: object) -> None:
        if "edge" not in ops:
            ops["edge"] = {"$each": []}

        edg_list: list = ops["edge"]["$each"]
        edg_list.append(up)

    def _access(self, ops: dict, access: str, target_id: ObjectId) -> None:
        if access not in ops:
            ops[access] = {"$each": set()}

        access_set: set = ops[access]["$each"]
        access_set.add(target_id)

    def update_context(self, up: dict) -> None:
        """Push update that there's a change happen in context."""
        self._set().update(up)

    def connect_edge(self, doc_anc: "DocAnchor") -> None:
        """Push update that there's newly added edge."""
        self._edge(self._push, doc_anc)

    def disconnect_edge(self, doc_anc: "DocAnchor") -> None:
        """Push update that there's edge that has been removed."""
        self._edge(self._pull, doc_anc)

    def allow_node(self, node_id: ObjectId) -> None:
        """Allow target node to access current Architype."""
        if node_id not in self.access.nodes:
            self.access.nodes.add(node_id)
            self._access(self._push, "access.nodes", node_id)

    def disallow_node(self, node_id: ObjectId) -> None:
        """Remove target node access from current Architype."""
        if node_id in self.access.nodes:
            self.access.nodes.remove(node_id)
            self._access(self._pull, "access.nodes", node_id)

    def allow_root(self, root_id: ObjectId) -> None:
        """Allow all access from target root graph to current Architype."""
        if root_id not in self.access.roots:
            self.access.roots.add(root_id)
            self._access(self._push, "access.roots", root_id)

    def disallow_root(self, root_id: ObjectId) -> None:
        """Disallow all access from target root graph to current Architype."""
        if root_id in self.access.roots:
            self.access.roots.remove(root_id)
            self._access(self._pull, "access.roots", root_id)

    def unrestrict(self) -> None:
        """Allow everyone to access current Architype."""
        if not self.access.all:
            self.access.all = True
            self._set.update({"access.all": True})

    def restrict(self) -> None:
        """Disallow others to access current Architype."""
        if self.access.all:
            self.access.all = False
            self._set.update({"access.all": False})

    def class_ref(self) -> "type":
        """Return generated class equivalent for DocAnchor."""
        return JCLASS[self.type.value].get(self.name)

    def pull_changes(self) -> dict:
        """Return changes and clear current reference."""
        changes = self.changes
        self.changes = {}
        return changes

    def build(self, **kwargs: "dict[str, Any]") -> object:
        """Return generated class instance equivalent for DocAnchor."""
        self.arch = self.class_ref()(**kwargs)
        self.arch._jac_doc_ = self
        return self.arch

    def json(self) -> dict:
        """Return in dictionary type."""
        return {"_id": self.id, "root": self.root, "access": self.access.json()}

    @classmethod
    def ref(cls, ref_id: str) -> Optional["DocAnchor"]:
        """Return DocAnchor instance if ."""
        if ref_id and (match := TARGET_NODE_REGEX.search(ref_id)):
            return cls(
                type=JTYPE_DICT[match.group(2)],
                name=match.group(1),
                id=ObjectId(match.group(3)),
            )
        return None

    async def connect(self) -> object:
        """Retrieve the Architype from db and return."""
        data = None
        jctx: JacContext = JCONTEXT.get()

        if obj := jctx.get(self.id):
            data = self.arch = obj
            return data

        cls = self.class_ref()
        if cls:
            data = self.arch = await cls.Collection.find_by_id(self.id)
            jctx.set(data._jac_doc_.id, data)
        return data


class DocArchitype:
    """DocAnchor Class Handler."""

    @property
    def _jac_doc_(self) -> DocAnchor:
        if isinstance(jd := getattr(self, "__jac_doc__", None), DocAnchor):
            return jd

        jctx: JacContext = JCONTEXT.get()
        self.__jac_doc__ = DocAnchor(
            type=self._jac_type_,
            name=self.__class__.__name__,
            root=jctx.get_root_id(),
            arch=self,
        )
        return self.__jac_doc__

    @_jac_doc_.setter
    def _jac_doc_(self, val: DocAnchor) -> None:
        self.__jac_doc__ = val

    def __setattr__(self, __name: str, __value: Any) -> None:  # noqa: ANN401
        """Catch variable set to include in changes holder for db updates."""
        if (
            isinstance(jd := getattr(self, "__jac_doc__", None), DocAnchor)
            and (fields := getattr(self, "_jac_fields_", None))
            and __name in fields
        ):
            jd.update_context({f"ctx.{__name}": __value})

        return super().__setattr__(__name, __value)

    async def propagate_save(self, changes: dict, session: ClientSession) -> None:
        """Propagate saving."""
        changes = deepcopy(changes)
        for ops in [changes.get("$pull", {}), changes.get("$push", {})]:
            for up in ops.values():
                for idx, doc_anc in enumerate(each := up["$each"]):
                    if not doc_anc.connected:
                        await doc_anc.arch.save(session)
                    each[idx] = doc_anc.ref_id
        return changes

    def __eq__(self, other: "DocArchitype") -> bool:
        """Override equal implementation."""
        if other.__class__ is self.__class__:
            sjd = self._jac_doc_
            ojd = other._jac_doc_

            return sjd.type == ojd.type and sjd.name == ojd.name and sjd.id == ojd.id

        return False

    def __hash__(self) -> int:
        """Override hash implementation."""
        return hash(self._jac_doc_.ref_id)


class NodeArchitype(_NodeArchitype, DocArchitype):
    """Overriden NodeArchitype."""

    _jac_type_ = JType.NODE

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)

    class Collection:
        """Default NodeArchitype Collection."""

        @classmethod
        def __document__(cls, doc: dict) -> "NodeArchitype":
            """Return parsed NodeArchitype from document."""
            access: dict = doc.get("access")
            return cls.build_node(
                DocAnchor(
                    type=JType.NODE,
                    name=cls.get_model("node"),
                    id=doc.get("_id"),
                    root=doc.get("root"),
                    access=DocAccess(
                        all=access.get("all"),
                        nodes=set(access.get("nodes")),
                        roots=set(access.get("roots")),
                    ),
                    connected=True,
                ),
                doc,
            )

    def connect_edge(self, edge: "EdgeArchitype") -> None:
        """Update DocAnchor that there's newly added edge."""
        if isinstance(jd := getattr(self, "__jac_doc__", None), DocAnchor):
            jd.connect_edge(edge._jac_doc_)

    def disconnect_edge(self, edge: "EdgeArchitype") -> None:
        """Update DocAnchor that there's edge that has been removed."""
        if isinstance(jd := getattr(self, "__jac_doc__", None), DocAnchor):
            jd.disconnect_edge(edge._jac_doc_)

    async def save(self, session: ClientSession = None) -> DocAnchor:
        """Upsert NodeArchitype."""
        if session:
            jd = self._jac_doc_
            if not jd.connected:
                try:
                    jd.connected = True
                    jd.changes = {}
                    edges = [
                        (await edge.save(session)).ref_id for edge in self._jac_.edges
                    ]
                    await self.Collection.insert_one(
                        {**jd.json(), "edge": edges, "context": asdict(self)},
                        session=session,
                    )
                except Exception:
                    jd.connected = False
                    raise
            elif changes := jd.pull_changes():
                try:
                    await self.Collection.update_by_id(
                        jd.id,
                        await self.propagate_save(changes, session),
                        session=session,
                    )
                except Exception:
                    jd.changes = changes
                    raise
        else:
            async with await ArchCollection.get_session() as session:
                async with session.start_transaction():
                    try:
                        await self.save(session)
                        await session.commit_transaction()
                    except Exception:
                        await session.abort_transaction()
                        logger.exception("Error saving node!")
                        raise

        return self._jac_doc_


@dataclass(eq=False)
class NodeAnchor(_NodeAnchor):
    """Overridden NodeAnchor."""

    async def get_edges(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list["EdgeArchitype"]], list["EdgeArchitype"]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list["EdgeArchitype"]:
        """Get edges connected to this node."""
        edge_list: list[EdgeArchitype] = [*self.edges]
        ret_edges: list[EdgeArchitype] = []

        jctx: JacContext = JCONTEXT.get()
        await jctx.populate([el for el in edge_list if isinstance(el, DocAnchor)])

        edge_list = [
            await el.connect() if isinstance(el, DocAnchor) else el for el in edge_list
        ]

        edge_list = filter_func(edge_list) if filter_func else edge_list
        for e in edge_list:
            if (
                e._jac_.target
                and e._jac_.source
                and (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self.obj == e._jac_.source
                    and (not target_obj or e._jac_.target in target_obj)
                )
                or (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self.obj == e._jac_.target
                    and (not target_obj or e._jac_.source in target_obj)
                )
            ):
                ret_edges.append(e)
        return ret_edges

    async def edges_to_nodes(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list["EdgeArchitype"]], list["EdgeArchitype"]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        edge_list: list[EdgeArchitype] = [*self.edges]
        node_list: list[NodeArchitype] = []

        jctx: JacContext = JCONTEXT.get()
        await jctx.populate([el for el in edge_list if isinstance(el, DocAnchor)])

        edge_list = [
            await el.connect() if isinstance(el, DocAnchor) else el for el in edge_list
        ]

        edge_list = filter_func(edge_list) if filter_func else edge_list

        for e in edge_list:
            if (tgt := e._jac_.target) and (src := e._jac_.source):
                if isinstance(tgt, DocAnchor):
                    e._jac_.target = await tgt.connect()
                if isinstance(src, DocAnchor):
                    e._jac_.source = await src.connect()

                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self.obj == e._jac_.source
                    and (not target_obj or e._jac_.target in target_obj)
                ):
                    node_list.append(e._jac_.target)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self.obj == e._jac_.target
                    and (not target_obj or e._jac_.source in target_obj)
                ):
                    node_list.append(e._jac_.source)
        return node_list


@dataclass(eq=False)
class Root(NodeArchitype, _Root):
    """Overridden Root."""

    _jac_type_: ClassVar[JType] = JType.ROOT

    def __init__(self) -> None:
        """Create Root."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)

    @classmethod
    async def register(cls, session: ClientSession = None) -> None:
        """Register Root."""
        root = cls()
        root_id = ObjectId()
        root._jac_doc_ = DocAnchor(
            type=JType.ROOT,
            name=root.__class__.__name__,
            id=root_id,
            root=root_id,
            arch=root,
        )
        return await root.save(session)

    class Collection(ArchCollection):
        """Default Root Collection."""

        __collection__ = "root"

        @classmethod
        def __document__(cls, doc: dict) -> "Root":
            """Return parsed NodeArchitype from document."""
            access: dict = doc.get("access")
            return cls.build_node(
                DocAnchor(
                    type=JType.ROOT,
                    name="root",
                    id=doc.get("_id"),
                    root=doc.get("root"),
                    access=DocAccess(
                        all=access.get("all"),
                        nodes=set(access.get("nodes")),
                        roots=set(access.get("roots")),
                    ),
                    connected=True,
                ),
                doc,
            )


class EdgeArchitype(_EdgeArchitype, DocArchitype):
    """Overriden EdgeArchitype."""

    _jac_type_ = JType.EDGE

    def __init__(self) -> None:
        """Create EdgeArchitype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)

    class Collection:
        """Default EdgeArchitype Collection."""

        @classmethod
        def __document__(cls, doc: dict) -> "EdgeArchitype":
            """Return parsed EdgeArchitype from document."""
            access: dict = doc.get("access")
            return cls.build_edge(
                DocAnchor(
                    type=JType.EDGE,
                    name=cls.get_model("edge"),
                    id=doc.get("_id"),
                    root=doc.get("root"),
                    access=DocAccess(
                        all=access.get("all"),
                        nodes=set(access.get("nodes")),
                        roots=set(access.get("roots")),
                    ),
                    connected=True,
                ),
                doc,
            )

    async def save(self, session: ClientSession = None) -> DocAnchor:
        """Upsert EdgeArchitype."""
        if session:
            jd = self._jac_doc_
            if not jd.connected:
                try:
                    jd.connected = True
                    jd.changes = {}
                    await self.Collection.insert_one(
                        {
                            **jd.json(),
                            "source": (await self._jac_.source.save(session)).ref_id,
                            "target": (await self._jac_.target.save(session)).ref_id,
                            "is_undirected": self._jac_.is_undirected,
                            "context": asdict(self),
                        },
                        session=session,
                    )
                except Exception:
                    jd.connected = False
                    raise
            elif changes := jd.pull_changes():
                try:
                    await self.Collection.update_by_id(
                        jd.id,
                        await self.propagate_save(changes, session),
                        session=session,
                    )
                except Exception:
                    jd.changes = changes
                    raise
        else:
            async with await ArchCollection.get_session() as session:
                async with session.start_transaction():
                    try:
                        await self.save(session)
                        await session.commit_transaction()
                    except Exception:
                        await session.abort_transaction()
                        logger.exception("Error saving edge!")
                        raise

        return self._jac_doc_


@dataclass(eq=False)
class EdgeAnchor(_EdgeAnchor):
    """Overriden EdgeAnchor."""

    def attach(
        self, src: NodeArchitype, trg: NodeArchitype, is_undirected: bool = False
    ) -> "EdgeAnchor":
        """Attach edge to nodes."""
        self.source = src
        self.target = trg
        self.is_undirected = is_undirected
        src._jac_.edges.append(self.obj)
        src.connect_edge(self.obj)
        trg._jac_.edges.append(self.obj)
        trg.connect_edge(self.obj)
        return self

    def detach(
        self, src: NodeArchitype, trg: NodeArchitype, is_undirected: bool = False
    ) -> "EdgeAnchor":
        """Detach edge from nodes."""
        self.source = src  # TODO: Delete me, don't keep attached
        self.target = trg  # TODO: Delete me, don't keep attached
        self.is_undirected = is_undirected
        src._jac_.edges.remove(self.obj)
        src.disconnect_edge(self.obj)
        trg._jac_.edges.remove(self.obj)
        trg.disconnect_edge(self.obj)
        return self


@dataclass(eq=False)
class GenericEdge(EdgeArchitype):
    """GenericEdge Replacement."""

    def __init__(self) -> None:
        """Create Generic Edge."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)

    class Collection(EdgeArchitype.Collection, ArchCollection):
        """Default GenericEdge Collection."""

        __collection__ = "e"

        @classmethod
        def __document__(cls, doc: dict) -> "EdgeArchitype":
            """Return parsed EdgeArchitype from document."""
            return cls.build_edge(
                DocAnchor(type=JType.EDGE, name="edge", id=doc.get("_id")),
                doc,
            )


class JacContext:
    """Jac Lang Context Handler."""

    def __init__(self, request: Request, entry: str = None) -> None:
        """Create JacContext."""
        self.__mem__: dict[ObjectId, object] = {}
        self.request = request
        self.user = getattr(request, "auth_user", None)
        self.root = getattr(request, "auth_root", base_root)
        self.reports = []
        self.entry = entry

    def get_root_id(self) -> ObjectId:
        """Retrieve Root Doc Id."""
        if self.root is base_root:
            return None
        return self.root._jac_doc_.id

    async def get_entry(self) -> NodeArchitype:
        """Retrieve Node Entry Point."""
        if isinstance(self.entry, str):
            if self.entry and (match := TARGET_NODE_REGEX.search(self.entry)):
                entry = await JCLASS[JTYPE_DICT[match.group(2)].value][
                    match.group(1)
                ].Collection.find_by_id(ObjectId(match.group(3)))
                if isinstance(entry, NodeArchitype):
                    self.entry = entry
                else:
                    self.entry = self.root
            else:
                self.entry = self.root
        elif self.entry is None:
            self.entry = self.root

        return self.entry

    async def populate(self, danchors: list[DocAnchor]) -> None:
        """Populate in-memory references."""
        queue = {}
        for danchor in danchors:
            if not self.has(danchor.id):
                cls = danchor.class_ref()
                if cls not in queue:
                    queue[cls] = {"_id": {"$in": []}}
                qin: list = queue[cls]["_id"]["$in"]
                qin.append(danchor.id)
        for cls, que in queue.items():
            for arch in await cls.Collection.find(que):
                self.set(arch._jac_doc_.id, arch)

    def has(self, id: Union[ObjectId, str]) -> bool:
        """Check if Architype is existing in memory."""
        return ObjectId(id) in self.__mem__

    def get(self, id: Union[ObjectId, str], default: object = None) -> object:
        """Retrieve Architype in memory."""
        return self.__mem__.get(ObjectId(id), default)

    def set(self, id: Union[ObjectId, str], obj: object) -> None:
        """Push Architype in memory via ID."""
        self.__mem__[ObjectId(id)] = obj

    def remove(self, id: Union[ObjectId, str]) -> object:
        """Pull Architype in memory via ID."""
        return self.__mem__.pop(ObjectId(id), None)

    def report(self, obj: Any) -> None:  # noqa: ANN401
        """Append report."""
        self.reports.append(obj)

    def response(self, ret: Any, status: int = 200) -> list:  # noqa: ANN401
        """Return serialized version of reports."""
        resp = {"status": status, "data": ret}

        if self.reports:
            for key, val in enumerate(self.reports):
                if isinstance(val, Architype) and (
                    ret_jd := getattr(val, "_jac_doc_", None)
                ):
                    self.reports[key] = {"id": ret_jd.ref_id, "ctx": asdict(val)}
                else:
                    self.clean_response(key, val, self.reports)
            resp["report"] = self.reports

        return resp

    def clean_response(
        self, key: str, val: Any, obj: Union[list, dict]  # noqa: ANN401
    ) -> None:
        """Cleanup and override current object."""
        if isinstance(val, list):
            for idx, lval in enumerate(val):
                self.clean_response(idx, lval, val)
        elif isinstance(val, dict):
            for key, dval in val.items():
                self.clean_response(key, dval, val)
        elif isinstance(val, Architype) and (ret_jd := getattr(val, "_jac_doc_", None)):
            obj[key] = {"id": ret_jd.ref_id, "context": asdict(val)}


Root.__name__ = "root"
GenericEdge.__name__ = "edge"

JCLASS = [{"root": Root}, {}, {"edge": GenericEdge}]
