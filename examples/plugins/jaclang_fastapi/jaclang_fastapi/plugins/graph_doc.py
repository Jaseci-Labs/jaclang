from jaclang.core.construct import Architype, DSFunc, EdgeDir

from typing import Type, Callable, Optional
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac

from .common import (
    NodeArchitype,
    EdgeArchitype,
    GenericEdge,
    JType,
    JCLASS,
    ArchCollection,
    EdgeAnchor,
)


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
            populate_collection(cls, JType.NODE)
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
            populate_collection(cls, JType.EDGE)
            return cls

        return decorator

    @staticmethod
    @hookimpl
    async def edge_ref(
        node_obj: NodeArchitype,
        dir: EdgeDir,
        filter_type: Optional[type],
        filter_func: Optional[Callable],
    ) -> list[NodeArchitype]:
        """Jac's apply_dir stmt feature."""
        if isinstance(node_obj, NodeArchitype):
            return await node_obj._jac_.edges_to_nodes(dir, filter_type, filter_func)
        else:
            raise TypeError("Invalid node object")

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


def populate_collection(cls: type, jtype: JType) -> type:
    class_name = cls.__name__.lower()
    JCLASS[jtype.value][class_name] = cls

    collection = f"{jtype}_{class_name}"
    if (coll := getattr(cls, "Collection", None)) is None:

        class Collection(ArchCollection):
            __collection__ = collection
            __excluded__ = []  # private fields
            __indexes__ = []  # not sure yet

        cls.Collection = Collection
    elif not issubclass(coll, ArchCollection):
        cls.Collection = type(
            coll.__name__, (coll, ArchCollection), {"__collection__": collection}
        )

    return cls
