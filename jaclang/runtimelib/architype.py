"""Core constructs for Jac Language."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from types import UnionType
from typing import Any, Callable, Iterable, Optional, Type, TypeVar, cast
from uuid import UUID, uuid4

from jaclang.compiler.constant import EdgeDir
from jaclang.runtimelib.utils import collect_node_connections

TARCH = TypeVar("TARCH", bound="Architype")
TANCH = TypeVar("TANCH", bound="Anchor")


@dataclass
class Report:
    """Report Handler."""

    id: str
    context: dict[str, Any]


@dataclass
class AnchorState:
    """Anchor state handler."""

    # None == do nothing
    # False == to be deleted
    # True == already deleted
    deleted: bool | None = None
    connected: bool = False
    persistent: bool = False
    hash: int = 0


@dataclass
class WalkerAnchorState(AnchorState):
    """Anchor state handler."""

    disengaged: bool = False


@dataclass(eq=False)
class Anchor:
    """Object Anchor."""

    name: str = ""
    id: UUID = field(default_factory=uuid4)
    architype: Optional[Architype] = None
    state: AnchorState = field(default_factory=AnchorState)

    @property
    def ref_id(self) -> str:
        """Return id in reference type."""
        return str(self.id)

    @classmethod
    def ref(cls: Type[TANCH], ref_id: str) -> TANCH | None:
        """Return Anchor instance if valid."""
        try:
            return cls(id=UUID(ref_id))
        except Exception:
            return None

    def unsync(self: TANCH) -> TANCH:
        """Return unsynced copy of anchor."""
        unsynced = object.__new__(self.__class__)
        unsynced.name = self.name
        unsynced.id = self.id
        unsynced.state = self.state.__class__()
        return unsynced

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[Architype]:
        """Retrieve the Architype from db and return."""
        if self.state.deleted is not None:
            return None

        from jaclang.plugin.feature import JacFeature as Jac

        ctx_mem = Jac.context().mem

        if anchor := ctx_mem.find_one(self.id):
            self.__dict__.update(anchor.__dict__)

        return self.architype

    def save(self) -> None:
        """Save Anchor."""
        from jaclang.plugin.feature import JacFeature as Jac

        self.state.persistent = True
        Jac.context().mem.set(self.id, self)

    def destroy(self) -> None:
        """Destroy Anchor."""
        if self.architype and self.state.deleted is None:
            from jaclang.plugin.feature import JacFeature as Jac

            self.state.deleted = False
            Jac.context().mem.remove(self.id)

    def unlinked_architype(self) -> Architype | None:
        """Unlink architype."""
        # this is to avoid using copy/deepcopy as it can be overriden by architypes in language level
        if self.architype:
            cloned = object.__new__(self.architype.__class__)
            cloned.__dict__.update(self.architype.__dict__)
            cloned.__dict__.pop("__jac__", None)
            return cloned
        return None

    def __getstate__(self) -> dict[str, object]:
        """Serialize Anchor."""
        state: dict[str, object] = {
            "name": self.name,
            "id": self.id,
            "state": self.state,
        }

        if architype := self.unlinked_architype():
            state["architype"] = architype

        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Deserialize Anchor."""
        self.__dict__.update(state)

        if self.architype:
            self.architype.__jac__ = self
        else:
            self.root = None
            self.architype = None

    def report(self) -> Report:
        """Report Anchor."""
        return Report(
            id=self.ref_id,
            context=(
                asdict(self.architype)
                if is_dataclass(self.architype) and not isinstance(self.architype, type)
                else {}
            ),
        )

    def __hash__(self) -> int:
        """Override hash for anchor."""
        return hash(self.ref_id)

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, Anchor):
            return (
                self.__class__ is other.__class__
                and self.name == other.name
                and self.id == other.id
                and self.architype == self.architype
            )

        return False


@dataclass(eq=False)
class NodeAnchor(Anchor):
    """Node Anchor."""

    architype: Optional[NodeArchitype] = None
    edges: list[EdgeAnchor] = field(default_factory=list)

    def connect_node(self, node: NodeAnchor, edge: EdgeAnchor) -> None:
        """Connect a node with given edge."""
        edge.attach(self, node)

    def get_edges(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[EdgeArchitype]:
        """Get edges connected to this node."""
        ret_edges: list[EdgeArchitype] = []
        for anchor in self.edges:
            if (
                (architype := anchor.sync(self))
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
                and (src_arch := source.sync())
                and (trg_arch := target.sync())
            ):
                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and (not target_obj or trg_arch in target_obj)
                ):
                    ret_edges.append(architype)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and (not target_obj or src_arch in target_obj)
                ):
                    ret_edges.append(architype)
        return ret_edges

    def edges_to_nodes(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        ret_edges: list[NodeArchitype] = []
        for anchor in self.edges:
            if (
                (architype := anchor.sync(self))
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
                and (src_arch := source.sync())
                and (trg_arch := target.sync())
            ):
                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and (not target_obj or trg_arch in target_obj)
                ):
                    ret_edges.append(trg_arch)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and (not target_obj or src_arch in target_obj)
                ):
                    ret_edges.append(src_arch)
        return ret_edges

    def remove_edge(self, edge: EdgeAnchor) -> None:
        """Remove reference without checking sync status."""
        for idx, ed in enumerate(self.edges):
            if ed.id == edge.id:
                self.edges.pop(idx)
                break

    def gen_dot(self, dot_file: Optional[str] = None) -> str:
        """Generate Dot file for visualizing nodes and edges."""
        visited_nodes: set[NodeAnchor] = set()
        connections: set[tuple[NodeArchitype, NodeArchitype, str]] = set()
        unique_node_id_dict = {}

        collect_node_connections(self, visited_nodes, connections)
        dot_content = 'digraph {\nnode [style="filled", shape="ellipse", fillcolor="invis", fontcolor="black"];\n'
        for idx, i in enumerate([nodes_.architype for nodes_ in visited_nodes]):
            unique_node_id_dict[i] = (i.__class__.__name__, str(idx))
            dot_content += f'{idx} [label="{i}"];\n'
        dot_content += 'edge [color="gray", style="solid"];\n'

        for pair in list(set(connections)):
            dot_content += (
                f"{unique_node_id_dict[pair[0]][1]} -> {unique_node_id_dict[pair[1]][1]}"
                f' [label="{pair[2]}"];\n'
            )
        if dot_file:
            with open(dot_file, "w") as f:
                f.write(dot_content + "}")
        return dot_content + "}"

    def spawn_call(self, walk: WalkerAnchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        return walk.spawn_call(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[NodeArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[NodeArchitype], super().sync(node))

    def destroy(self) -> None:
        """Destroy Anchor."""
        if self.architype and self.state.deleted is None:
            from jaclang.plugin.feature import JacFeature as Jac

            self.state.deleted = False
            for edge in self.edges:
                edge.destroy()
            Jac.context().mem.remove(self.id)

    def __getstate__(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        state = super().__getstate__()

        if self.architype:
            state["edges"] = [edge.unsync() for edge in self.edges]

        return state


@dataclass(eq=False)
class EdgeAnchor(Anchor):
    """Edge Anchor."""

    architype: Optional[EdgeArchitype] = None
    source: Optional[NodeAnchor] = None
    target: Optional[NodeAnchor] = None
    is_undirected: bool = False

    def attach(
        self, src: NodeAnchor, trg: NodeAnchor, is_undirected: bool = False
    ) -> EdgeAnchor:
        """Attach edge to nodes."""
        self.source = src
        self.target = trg
        self.is_undirected = is_undirected
        src.edges.append(self)
        trg.edges.append(self)
        return self

    def detach(self) -> None:
        """Detach edge from nodes."""
        if source := self.source:
            source.remove_edge(self)
        if target := self.target:
            target.remove_edge(self)

    def spawn_call(self, walk: WalkerAnchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if target := self.target:
            return walk.spawn_call(target)
        else:
            raise ValueError("Edge has no target.")

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[EdgeArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[EdgeArchitype], super().sync(node))

    def destroy(self) -> None:
        """Destroy Anchor."""
        if self.architype and self.state.deleted is None:
            from jaclang.plugin.feature import JacFeature as Jac

            self.state.deleted = False
            self.detach()
            Jac.context().mem.remove(self.id)

    def __getstate__(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        state = super().__getstate__()

        if self.architype:
            state.update(
                {
                    "source": self.source.unsync() if self.source else None,
                    "target": self.target.unsync() if self.target else None,
                    "is_undirected": self.is_undirected,
                }
            )

        return state


@dataclass(eq=False)
class WalkerAnchor(Anchor):
    """Walker Anchor."""

    architype: Optional[WalkerArchitype] = None
    path: list[Anchor] = field(default_factory=list)
    next: list[Anchor] = field(default_factory=list)
    ignores: list[Anchor] = field(default_factory=list)
    state: WalkerAnchorState = field(default_factory=WalkerAnchorState)

    def visit_node(self, anchors: Iterable[NodeAnchor | EdgeAnchor]) -> bool:
        """Walker visits node."""
        before_len = len(self.next)
        for anchor in anchors:
            if anchor not in self.ignores:
                if isinstance(anchor, NodeAnchor):
                    self.next.append(anchor)
                elif isinstance(anchor, EdgeAnchor):
                    if anchor.sync() and (target := anchor.target):
                        self.next.append(target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.next) > before_len

    def ignore_node(self, anchors: Iterable[NodeAnchor | EdgeAnchor]) -> bool:
        """Walker ignores node."""
        before_len = len(self.ignores)
        for anchor in anchors:
            if anchor not in self.ignores:
                if isinstance(anchor, NodeAnchor):
                    self.ignores.append(anchor)
                elif isinstance(anchor, EdgeAnchor):
                    if anchor.sync() and (target := anchor.target):
                        self.ignores.append(target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.ignores) > before_len

    def disengage_now(self) -> None:
        """Disengage walker from traversal."""
        self.state.disengaged = True

    def spawn_call(self, node: Anchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if walker := self.sync():
            self.path = []
            self.next = [node]
            while len(self.next):
                if current_node := self.next.pop(0).sync():
                    for i in current_node._jac_entry_funcs_:
                        if not i.trigger or isinstance(walker, i.trigger):
                            if i.func:
                                i.func(current_node, walker)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in walker._jac_entry_funcs_:
                        if not i.trigger or isinstance(current_node, i.trigger):
                            if i.func:
                                i.func(walker, current_node)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in walker._jac_exit_funcs_:
                        if not i.trigger or isinstance(current_node, i.trigger):
                            if i.func:
                                i.func(walker, current_node)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in current_node._jac_exit_funcs_:
                        if not i.trigger or isinstance(walker, i.trigger):
                            if i.func:
                                i.func(current_node, walker)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
            self.ignores = []
            return walker
        raise Exception(f"Invalid Reference {self.ref_id}")

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[WalkerArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[WalkerArchitype], super().sync(node))


class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: list[DSFunc]
    _jac_exit_funcs_: list[DSFunc]

    def __init__(self) -> None:
        """Create default architype."""
        self.__jac__ = Anchor(architype=self)

    def __repr__(self) -> str:
        """Override repr for architype."""
        return f"{self.__class__.__name__}"


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    __jac__: NodeAnchor

    def __init__(self) -> None:
        """Create node architype."""
        self.__jac__ = NodeAnchor(name=self.__class__.__name__, architype=self)


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    __jac__: EdgeAnchor

    def __init__(self) -> None:
        """Create edge architype."""
        self.__jac__ = EdgeAnchor(name=self.__class__.__name__, architype=self)


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    __jac__: WalkerAnchor

    def __init__(self) -> None:
        """Create walker architype."""
        self.__jac__ = WalkerAnchor(name=self.__class__.__name__, architype=self)


class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []

    def __init__(self) -> None:
        """Create generic edge architype."""
        self.__jac__ = EdgeAnchor(architype=self)


class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []
    reachable_nodes: list[NodeArchitype] = []
    connections: set[tuple[NodeArchitype, NodeArchitype, EdgeArchitype]] = set()

    def __init__(self) -> None:
        """Create root node."""
        self.__jac__ = NodeAnchor(id=UUID(int=0), architype=self)
        self.__jac__.state.persistent = True

    def reset(self) -> None:
        """Reset the root."""
        self.reachable_nodes = []
        self.connections = set()
        self.__jac__.edges = []


@dataclass(eq=False)
class DSFunc:
    """Data Spatial Function."""

    name: str
    trigger: type | UnionType | tuple[type | UnionType, ...] | None
    func: Callable[[Any, Any], Any] | None = None

    def resolve(self, cls: type) -> None:
        """Resolve the function."""
        self.func = getattr(cls, self.name)
