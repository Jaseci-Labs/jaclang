from contextvars import ContextVar
from jaclang.core.construct import (
    Architype,
    NodeArchitype as _NodeArchitype,
    EdgeArchitype as _EdgeArchitype,
    NodeAnchor as _NodeAnchor,
    EdgeAnchor as _EdgeAnchor,
    EdgeDir,
    Root as _Root,
    root,
)

from bson import ObjectId
from enum import Enum
from pymongo.client_session import ClientSession

from dataclasses import field, dataclass, asdict, fields
from typing import Union, Optional, Callable, Any

from fastapi import Request

from jaclang_fastapi.models import User
from jaclang_fastapi.collections import BaseCollection
from jaclang_fastapi.utils import logger

JCONTEXT = ContextVar("JCONTEXT")
JTYPE = ["r", "n", "e"]


class JType(Enum):
    ROOT = 0
    NODE = 1
    EDGE = 2

    def __str__(self):
        return JTYPE[self.value]


class ArchCollection(BaseCollection):
    @classmethod
    def translate_edges(cls, edges: list[list[dict]]):
        doc_edges: dict[EdgeDir, list[DocAnchor]] = {EdgeDir.IN: [], EdgeDir.OUT: []}
        for i, es in enumerate(edges):
            for e in es:
                doc_edges[EdgeDir(i)].append(
                    DocAnchor(
                        type=JType(e.get("_type")), name=e.get("_name"), id=e.get("_id")
                    )
                )
        return doc_edges


@dataclass(eq=False)
class DocAnchor:
    type: JType
    name: str
    id: ObjectId
    obj: object = None
    changes: Optional[dict] = field(default_factory=dict)

    def update(self, up: dict):
        if "$set" not in self.changes:
            self.changes["$set"] = {}

        _set: dict = self.changes.get("$set")
        _set.update(up)

    def edge_push(self, dir: int, up: object):
        if "$push" not in self.changes:
            self.changes["$push"] = {}

        _push: dict = self.changes.get("$push")

        edg_tgt: str = f"edg.{dir}"
        if edg_tgt not in _push:
            _push[edg_tgt] = {"$each": []}

        edg_list: list = _push[edg_tgt]["$each"]
        edg_list.append(up)

    def edge_pull(self, dir: int, up: object):
        if "$pull" not in self.changes:
            self.changes["$pull"] = {}

        _pull: dict = self.changes.get("$pull")

        edg_tgt: str = f"edge.{dir}"
        if edg_tgt not in _pull:
            _pull[edg_tgt] = {"$each": []}

        edg_list: list = _pull[edg_tgt]["$each"]
        edg_list.append(up)

    def dict(self):
        return {"_id": self.id, "_type": self.type.value, "_name": self.name}

    def json(self):
        return {"_id": str(self.id), "_type": self.type.value, "_name": self.name}

    def class_ref(self):
        return JCLASS[self.type.value].get(self.name)

    def build(self, **kwargs):
        return self.class_ref()(**kwargs)

    def __dict__(self):
        return self.json()

    async def connect(self):
        cls = self.class_ref()
        data = None
        if cls:
            data = self.obj = await cls.Collection.find_by_id(self.id)
        return data


class NodeArchitype(_NodeArchitype):
    """Node Architype Protocol."""

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor

    def __setattr__(self, __name: str, __value: Any) -> None:
        jd: DocAnchor
        if (
            (jd := getattr(self, "_jac_doc_", None))
            and (fields := getattr(self, "_jac_fields_", None))
            and __name in fields
        ):
            jd.update({f"ctx.{__name}": __value})

        return super().__setattr__(__name, __value)

    class Collection:

        @classmethod
        def __document__(cls, doc: dict):
            doc_anc = DocAnchor(
                type=JType(doc.get("_type")), name=doc.get("_name"), id=doc.get("_id")
            )
            arch: NodeArchitype = doc_anc.build(**(doc.get("ctx") or {}))
            arch._jac_doc_ = doc_anc
            arch._jac_.edges = cls.translate_edges(doc.get("edg") or [])
            doc_anc.obj = arch._jac_
            return arch

    def update(self, up: dict):
        self._jac_doc_.update(up)

    def edge_push(self, dir: int, up: dict):
        self._jac_doc_.edge_push(dir, up)

    def edge_pull(self, dir: int, up: dict):
        self._jac_doc_.edge_pull(dir, up)

    async def _save(self, jtype: JType, session: ClientSession = None):
        if session:
            jd: DocAnchor
            if not (jd := getattr(self, "_jac_doc_", None)):
                self._jac_doc_ = DocAnchor(
                    jtype, self.__class__.__name__, ObjectId(), obj=self._jac_
                )
                edges = [[], [], [], []]  # can be used in future
                for edir, earchs in self._jac_.edges.items():
                    for earch in earchs:
                        edges[edir.value].append((await earch.save(session)).dict())

                await self.Collection.insert_one(
                    {**self._jac_doc_.dict(), "edg": edges, "ctx": asdict(self)},
                    session=session,
                )
            elif changes := jd.changes:
                jd.changes = {}
                for val in (changes.get("$push") or {}).values():
                    each = val.get("$each") or []
                    for idx, eval in enumerate(each):
                        if isinstance(eval, EdgeArchitype):
                            each[idx] = (await eval.save(session)).dict()

                await self.Collection.update_by_id(
                    jd.id,
                    changes,
                    session=session,
                )
        else:
            async with await ArchCollection.get_session() as session:
                async with session.start_transaction():
                    try:
                        await self._save(jtype, session)
                        await session.commit_transaction()
                    except Exception:
                        await session.abort_transaction()
                        logger.exception("Error saving node!")
                        raise

        return self._jac_doc_

    async def save(self, session: ClientSession = None):
        return await self._save(JType.NODE, session)


@dataclass(eq=False)
class NodeAnchor(_NodeAnchor):

    async def edges_to_nodes(
        self, dir: EdgeDir, filter_type: Optional[type], filter_func: Optional[Callable]
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        filter_func = filter_func or (lambda x: x)

        edge_list = []
        edges_dir = self.edges[dir]
        for idx, e in enumerate(edges_dir):
            if isinstance(e, DocAnchor):
                edges_dir[idx] = e = await e.connect()

            if getattr(
                e._jac_, "target" if dir == EdgeDir.OUT else "source", None
            ) and (not filter_type or isinstance(e, filter_type)):
                edge_list.append(e)

        node_list = []
        for e in filter_func(edge_list):
            ej = e._jac_
            ejt = ej.target
            ejs = ej.source

            if dir == EdgeDir.OUT:
                if isinstance(ejt, DocAnchor):
                    ej.target = ejt = await ejt.connect()
                node_list.append(ejt)
            else:
                if isinstance(ejs, DocAnchor):
                    ej.source = ejs = await ejs.connect()
                node_list.append(ejs)
        return node_list


@dataclass
class Root(NodeArchitype, _Root):
    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor

    async def save(self, session: ClientSession = None):
        return await self._save(JType.ROOT, session)

    class Collection(ArchCollection):
        __collection__ = f"root"

        @classmethod
        def __document__(cls, doc: dict):
            root = Root()
            root._jac_doc_ = DocAnchor(
                type=JType(doc.get("_type")),
                name=doc.get("_name"),
                id=doc.get("_id"),
                obj=root._jac_,
            )
            root._jac_.edges = cls.translate_edges(doc.get("edg") or [])
            return root


class EdgeArchitype(_EdgeArchitype):
    """Edge Architype Protocol."""

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)
        self._jac_doc_: DocAnchor

    def __setattr__(self, __name: str, __value: Any) -> None:
        jd: DocAnchor
        if (
            (jd := getattr(self, "_jac_doc_", None))
            and (fields := getattr(self, "_jac_fields_", None))
            and __name in fields
        ):
            jd.update({f"ctx.{__name}": __value})
        return super().__setattr__(__name, __value)

    class Collection:
        @classmethod
        def __document__(cls, doc: dict):
            doc_anc = DocAnchor(
                type=JType(doc.get("_type")), name=doc.get("_name"), id=doc.get("_id")
            )
            arch: EdgeArchitype = doc_anc.build(**(doc.get("ctx") or {}))
            arch._jac_doc_ = doc_anc
            if src := doc.get("src"):
                arch._jac_.source = DocAnchor(
                    type=JType(src.get("_type")),
                    name=src.get("_name"),
                    id=src.get("_id"),
                )

            if tgt := doc.get("tgt"):
                arch._jac_.target = DocAnchor(
                    type=JType(tgt.get("_type")),
                    name=tgt.get("_name"),
                    id=tgt.get("_id"),
                )

            doc_anc.obj = arch._jac_
            return arch

    async def save(self, session: ClientSession = None):
        if session:
            jd: DocAnchor
            if not (jd := getattr(self, "_jac_doc_", None)):
                self._jac_doc_ = DocAnchor(
                    JType.EDGE, self.__class__.__name__, ObjectId(), obj=self._jac_
                )

                await self.Collection.insert_one(
                    {
                        **self._jac_doc_.dict(),
                        "src": (await self._jac_.source.save(session)).dict(),
                        "tgt": (await self._jac_.target.save(session)).dict(),
                        "dir": self._jac_.dir.value,
                        "ctx": asdict(self),
                    },
                    session=session,
                )
            elif changes := jd.changes:
                jd.changes = {}
                await self.Collection.update_by_id(
                    jd.id,
                    {"$set": changes},
                    session=session,
                )
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
    def attach(self, src: NodeArchitype, trg: NodeArchitype) -> "EdgeAnchor":
        """Attach edge to nodes."""
        if self.dir == EdgeDir.IN:
            self.source = trg
            self.target = src
            self.source._jac_.edges[EdgeDir.IN].append(self.obj)
            self.target._jac_.edges[EdgeDir.OUT].append(self.obj)
            self.source.edge_push(EdgeDir.IN.value, self.obj)
            self.target.edge_push(EdgeDir.OUT.value, self.obj)
        else:
            self.source = src
            self.target = trg
            self.source._jac_.edges[EdgeDir.OUT].append(self.obj)
            self.target._jac_.edges[EdgeDir.IN].append(self.obj)
            self.source.edge_push(EdgeDir.OUT.value, self.obj)
            self.target.edge_push(EdgeDir.IN.value, self.obj)

        return self


@dataclass
class GenericEdge(EdgeArchitype):

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)
        self._jac_doc_: DocAnchor

    class Collection(EdgeArchitype.Collection, ArchCollection):
        __collection__ = f"e"


class JacContext:
    def __init__(self, request: Request):
        self.__mem__ = {}
        self.request = request
        self.user = getattr(request, "auth_user", None)
        self.root = getattr(request, "auth_root", root)
        self.reports = []

    def has(self, id: Union[ObjectId, str]):
        return str(id) in self.__mem__

    def get(self, id: Union[ObjectId, str], default: object = None):
        return self.__mem__.get(str(id), default)

    def set(self, id: Union[ObjectId, str], obj: object):
        self.__mem__[str(id)] = obj

    def remove(self, id: Union[ObjectId, str]):
        self.__mem__.pop(str(id), None)

    def report(self, obj: Any):
        self.reports.append(obj)

    def response(self):
        for key, val in enumerate(self.reports):
            if isinstance(val, Architype) and (
                ret_jd := getattr(val, "_jac_doc_", None)
            ):
                self.reports[key] = {**ret_jd.json(), "ctx": asdict(val)}
            else:
                self.clean_response(val)
        return self.reports

    def clean_response_override(self, key, val, obj):
        if isinstance(val, Architype) and (ret_jd := getattr(val, "_jac_doc_", None)):
            obj[key] = {**ret_jd.json(), "ctx": asdict(val)}

    def clean_response(self, obj: Union[list, dict]):
        if isinstance(obj, list):
            for idx, val in enumerate(obj):
                self.clean_response_override(idx, val, obj)

        elif isinstance(obj, dict):
            for key, val in obj.items():
                self.clean_response_override(key, val, obj)


JCLASS = [{Root.__name__: Root}, {}, {GenericEdge.__name__: GenericEdge}]
