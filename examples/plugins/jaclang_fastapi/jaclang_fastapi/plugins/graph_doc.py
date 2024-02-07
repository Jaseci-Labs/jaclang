from jaclang.core.construct import (
    Architype,
    DSFunc,
    NodeArchitype,
    EdgeArchitype,
    EdgeAnchor,
    NodeAnchor,
    ElementAnchor,
)

from bson import ObjectId

from dataclasses import field, dataclass
from typing import Type, Callable, Union, Optional
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from jaclang_fastapi.collections import BaseCollection


@dataclass(eq=False)
class DocAnchor:
    type: str
    id: Optional[ObjectId] = field(default=None)
    update: list[str] = field(default_factory=list)


class NodeArchitypeDoc(NodeArchitype):
    """Node Architype Protocol."""

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("node")
        self.Collection: BaseCollection

    async def save(self):
        if not self._jac_doc_.id:
            edges = [None, [], [], []]  # can be used in future
            for edir, earchs in self._jac_.edges.items():
                for earch in earchs:
                    edges[edir.value].append(earch.save())
            import pdb

            pdb.set_trace()
            self.Collection.insert_one({})

        return self._jac_doc_.id


class EdgeArchitypeDoc(EdgeArchitype):
    """Edge Architype Protocol."""

    def __init__(self) -> None:
        """Edge node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)
        self._jac_doc_: DocAnchor = DocAnchor("edge")
        self.Collection: BaseCollection

    def save(self: EdgeArchitype):
        if not self._jac_doc_.id:
            from uuid import uuid4
            from bson import ObjectId

            self._jac_doc_.id = ObjectId(str(uuid4()))

        return self._jac_doc_.id


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
                cls, arch_base=NodeArchitypeDoc, on_entry=on_entry, on_exit=on_exit
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
                cls, arch_base=EdgeArchitypeDoc, on_entry=on_entry, on_exit=on_exit
            )
            populate_collection(cls, "e")
            return cls

        return decorator


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
