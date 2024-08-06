"""Core constructs for Jac Language."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from os import getenv
from re import IGNORECASE, compile
from types import UnionType
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Optional,
    Type,
    TypeVar,
    cast,
    get_type_hints,
)
from uuid import UUID, uuid4

from jaclang.compiler.constant import EdgeDir
from jaclang.runtimelib.utils import collect_node_connections

from orjson import dumps

GENERIC_ID_REGEX = compile(
    r"^(g|n|e|w):([^:]*):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    IGNORECASE,
)
NODE_ID_REGEX = compile(
    r"^n:([^:]*):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    IGNORECASE,
)
EDGE_ID_REGEX = compile(
    r"^e:([^:]*):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    IGNORECASE,
)
WALKER_ID_REGEX = compile(
    r"^w:([^:]*):([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    IGNORECASE,
)
MANUAL_SAVE = getenv("ENABLE_MANUAL_SAVE") == "true"
TA = TypeVar("TA", bound="type[Architype]")


def populate_dataclasses(cls: type, attributes: dict[str, Any]) -> dict[str, Any]:
    """Populate nested dataclasses."""
    from dacite import from_dict

    if is_dataclass(cls) and issubclass(cls, Architype):
        for attr in fields(cls):
            if is_dataclass(
                field_type := cls.__jac_hintings__[attr.name]
            ) and isinstance(field_type, type):
                attributes[attr.name] = from_dict(field_type, attributes[attr.name])
    return attributes


class AnchorType(Enum):
    """Enum For Anchor Types."""

    generic = "g"
    node = "n"
    edge = "e"
    walker = "w"


@dataclass
class Access:
    """Access Structure."""

    whitelist: bool = True  # whitelist or blacklist
    anchors: dict[str, int] = field(default_factory=dict)

    def check(
        self, anchor: str
    ) -> tuple[bool, int]:  # whitelist or blacklist, has_read_access, level
        """Validate access."""
        if self.whitelist:
            return self.whitelist, self.anchors.get(anchor, -1)
        else:
            return self.whitelist, self.anchors.get(anchor, 2)


@dataclass
class Permission:
    """Anchor Access Handler."""

    all: int = -1
    roots: Access = field(default_factory=Access)
    # types: dict[type[Architype], Access] = field(default_factory=dict)
    # nodes: Access = field(default_factory=Access)

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Permission:
        """Deserialize Permission."""
        # types = cast(dict[str, dict[str, Any]], data.get("types", {}))
        return Permission(
            all=data.get("all", -1),
            roots=Access(**data.get("roots", {})),
            # types={
            #     (
            #         NodeArchitype.get(key[2:])
            #         if key[0] == "n"
            #         else EdgeArchitype.get(key[2:])
            #     ): Access(**value)
            #     for key, value in types.items()
            # },
            # nodes=Access(**data.get("nodes", {})),
        )


@dataclass
class AnchorState:
    """Anchor state handler."""

    connected: bool = False
    current_access_level: int = -1
    persistent: bool = field(default=not MANUAL_SAVE)
    hash: int = 0


@dataclass
class WalkerAnchorState(AnchorState):
    """Anchor state handler."""

    disengaged: bool = False
    persistent: bool = False  # disabled by default


@dataclass(eq=False)
class Anchor:
    """Object Anchor."""

    type: ClassVar[AnchorType] = AnchorType.generic
    name: str = ""
    id: UUID = field(default_factory=uuid4)
    root: Optional[UUID] = None
    access: Permission = field(default_factory=Permission)
    architype: Optional[Architype] = None
    state: AnchorState = field(default_factory=AnchorState)

    @property
    def ref_id(self) -> str:
        """Return id in reference type."""
        return f"{self.type.value}:{self.name}:{self.id}"

    @staticmethod
    def ref(ref_id: str) -> Optional[Anchor]:
        """Return ObjectAnchor instance if ."""
        if matched := GENERIC_ID_REGEX.search(ref_id):
            cls: type = Anchor
            match AnchorType(matched.group(1)):
                case AnchorType.node:
                    cls = NodeAnchor
                case AnchorType.edge:
                    cls = EdgeAnchor
                case AnchorType.walker:
                    cls = WalkerAnchor
                case _:
                    pass
            return cls(name=matched.group(2), id=UUID(matched.group(3)))
        return None

    def _save(self) -> None:
        """Save Anchor."""
        raise NotImplementedError("_save must be implemented in subclasses")

    def save(self) -> None:
        """Save Anchor."""
        if self.architype:
            if not self.state.connected:
                self.state.connected = True
                self.sync_hash()
                self._save()
            elif self.state.current_access_level > 0 and self.state.hash != (
                _hash := self.data_hash()
            ):
                self.state.hash = _hash
                self._save()

    def destroy(self) -> None:
        """Save Anchor."""
        raise NotImplementedError("destroy must be implemented in subclasses")

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[Architype]:
        """Retrieve the Architype from db and return."""
        if architype := self.architype:
            if (node or self).has_read_access(self):
                return architype
            return None

        from .context import ExecutionContext

        jsrc = ExecutionContext.get_or_create().datasource
        anchor = jsrc.find_one(self.id)

        if anchor and (node or self).has_read_access(anchor):
            self.__dict__.update(anchor.__dict__)

        return self.architype

    def allocate(self) -> None:
        """Allocate hashes and memory."""
        from .context import ExecutionContext

        jctx = ExecutionContext.get_or_create()
        if self.root is None and not isinstance(self.architype, Root):
            self.root = jctx.root.id
        jctx.datasource.set(self, True)

    def has_read_access(self, to: Anchor) -> bool:
        """Read Access Validation."""
        return self.access_level(to) > -1

    def has_connect_access(self, to: Anchor) -> bool:
        """Write Access Validation."""
        return self.access_level(to) > 0

    def has_write_access(self, to: Anchor) -> bool:
        """Write Access Validation."""
        return self.access_level(to) > 1

    def access_level(self, to: Anchor) -> int:
        """Access validation."""
        from .context import ExecutionContext

        jctx = ExecutionContext.get_or_create()
        jroot = jctx.root
        to.state.current_access_level = -1

        if jroot == jctx.super_root or jroot.id == to.root or jroot == to:
            to.state.current_access_level = 2

        if (to_access := to.access).all > -1:
            to.state.current_access_level = to_access.all

        # whitelist, level = to_access.nodes.check(self)
        # if not whitelist and level < 0:
        #     to.state.current_access_level = -1
        #     return to.state.current_access_level
        # elif whitelist and level > -1:
        #     to.state.current_access_level = level

        # if (architype := self.architype) and (
        #     access_type := to_access.types.get(architype.__class__)
        # ):
        #     whitelist, level = access_type.check(self)
        #     if not whitelist and level < 0:
        #         to.state.current_access_level = -1
        #         return to.state.current_access_level
        #     elif whitelist and level > -1 and to.state.current_access_level == -1:
        #         to.state.current_access_level = level

        whitelist, level = to_access.roots.check(jroot.ref_id)
        if not whitelist and level < 0:
            to.state.current_access_level = -1
            return to.state.current_access_level
        elif whitelist and level > -1 and to.state.current_access_level == -1:
            to.state.current_access_level = level

        if to.root and (to_root := jctx.datasource.find_one(to.root)):
            whitelist, level = to_root.access.roots.check(jroot.ref_id)
            if not whitelist and level < 0:
                to.state.current_access_level = -1
                return to.state.current_access_level
            elif whitelist and level > -1 and to.state.current_access_level == -1:
                to.state.current_access_level = level

        return to.state.current_access_level

    def serialize(self) -> dict[str, object]:
        """Serialize Anchor."""
        return {
            "type": self.type.value,
            "name": self.name,
            "id": self.id,
            "root": self.root,
            "access": asdict(self.access),
            "architype": (
                asdict(self.architype)
                if is_dataclass(self.architype) and not isinstance(self.architype, type)
                else {}
            ),
        }

    def data_hash(self) -> int:
        """Get current serialization hash."""
        return hash(dumps(self.serialize()))

    def sync_hash(self) -> None:
        """Sync current serialization hash."""
        self.state.hash = self.data_hash()

    def report(self) -> dict[str, object]:
        """Report Anchor."""
        return {
            "id": self.ref_id,
            "context": (
                asdict(self.architype)
                if is_dataclass(self.architype) and not isinstance(self.architype, type)
                else {}
            ),
        }

    def __hash__(self) -> int:
        """Override hash for anchor."""
        return hash(self.ref_id)

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, Anchor):
            return (
                self.type == other.type
                and self.name == other.name
                and self.id == other.id
                and self.architype == self.architype
                and self.state.connected == other.state.connected
            )
        elif isinstance(other, Architype):
            return self == other.__jac__

        return False


@dataclass(eq=False)
class NodeAnchor(Anchor):
    """Node Anchor."""

    type: ClassVar[AnchorType] = AnchorType.node
    architype: Optional[NodeArchitype] = None
    edges: list[EdgeAnchor] = field(default_factory=list)

    @classmethod
    def ref(cls, ref_id: str) -> Optional[NodeAnchor]:
        """Return NodeAnchor instance if existing."""
        if match := NODE_ID_REGEX.search(ref_id):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        jsrc = ExecutionContext.get_or_create().datasource

        for edge in self.edges:
            edge.save()

        jsrc.set(self)

    def destroy(self) -> None:
        """Delete Anchor."""
        if self.architype and self.state.current_access_level > 1:
            from .context import ExecutionContext

            jsrc = ExecutionContext.get_or_create().datasource
            for edge in self.edges:
                edge.destroy()

            jsrc.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[NodeArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[NodeArchitype], super().sync(node))

    def connect_node(self, nd: NodeAnchor, edg: EdgeAnchor) -> None:
        """Connect a node with given edge."""
        edg.attach(self, nd)

    def get_edges(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_cls: Optional[list[Type[NodeArchitype]]],
    ) -> list[EdgeArchitype]:
        """Get edges connected to this node."""
        ret_edges: list[EdgeArchitype] = []
        for anchor in self.edges:
            if (
                (architype := anchor.sync(self))
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
            ):
                src_arch = source.sync()
                trg_arch = target.sync()

                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and trg_arch
                    and (not target_cls or trg_arch.__class__ in target_cls)
                    and source.has_read_access(target)
                ):
                    ret_edges.append(architype)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and src_arch
                    and (not target_cls or src_arch.__class__ in target_cls)
                    and target.has_read_access(source)
                ):
                    ret_edges.append(architype)
        return ret_edges

    def edges_to_nodes(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_cls: Optional[list[Type[NodeArchitype]]],
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        ret_edges: list[NodeArchitype] = []
        for anchor in self.edges:
            if (
                (architype := anchor.sync(self))
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
            ):
                src_arch = source.sync()
                trg_arch = target.sync()

                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and trg_arch
                    and (not target_cls or trg_arch.__class__ in target_cls)
                    and source.has_read_access(target)
                ):
                    ret_edges.append(trg_arch)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and src_arch
                    and (not target_cls or src_arch.__class__ in target_cls)
                    and target.has_read_access(source)
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

    def serialize(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        return {**super().serialize(), "edges": [edge.ref_id for edge in self.edges]}


@dataclass(eq=False)
class EdgeAnchor(Anchor):
    """Edge Anchor."""

    type: ClassVar[AnchorType] = AnchorType.edge
    architype: Optional[EdgeArchitype] = None
    source: Optional[NodeAnchor] = None
    target: Optional[NodeAnchor] = None
    is_undirected: bool = False

    @classmethod
    def ref(cls, ref_id: str) -> Optional[EdgeAnchor]:
        """Return EdgeAnchor instance if existing."""
        if match := EDGE_ID_REGEX.search(ref_id):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        jsrc = ExecutionContext.get_or_create().datasource

        if source := self.source:
            source.save()

        if target := self.target:
            target.save()

        jsrc.set(self)

    def destroy(self) -> None:
        """Delete Anchor."""
        if self.architype and self.state.current_access_level > 1:
            from .context import ExecutionContext

            jsrc = ExecutionContext.get_or_create().datasource

            source = self.source
            target = self.target
            self.detach()

            if source:
                source.save()
            if target:
                target.save()

            jsrc.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[EdgeArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[EdgeArchitype], super().sync(node))

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

        self.source = None
        self.target = None

    def spawn_call(self, walk: WalkerAnchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if target := self.target:
            return walk.spawn_call(target)
        else:
            raise ValueError("Edge has no target.")

    def serialize(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        return {
            **super().serialize(),
            "source": self.source.ref_id if self.source else None,
            "target": self.target.ref_id if self.target else None,
        }


@dataclass(eq=False)
class WalkerAnchor(Anchor):
    """Walker Anchor."""

    type: ClassVar[AnchorType] = AnchorType.walker
    architype: Optional[WalkerArchitype] = None
    path: list[Anchor] = field(default_factory=list)
    next: list[Anchor] = field(default_factory=list)
    ignores: list[Anchor] = field(default_factory=list)
    state: WalkerAnchorState = field(default_factory=WalkerAnchorState)

    @classmethod
    def ref(cls, ref_id: str) -> Optional[WalkerAnchor]:
        """Return EdgeAnchor instance if existing."""
        if ref_id and (match := WALKER_ID_REGEX.search(ref_id)):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        ExecutionContext.get_or_create().datasource.set(self)

    def destroy(self) -> None:
        """Delete Anchor."""
        if self.architype and self.state.current_access_level > 1:
            from .context import ExecutionContext

            ExecutionContext.get_or_create().datasource.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[WalkerArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[WalkerArchitype], super().sync(node))

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

    def spawn_call(self, nd: Anchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if walker := self.sync():
            self.path = []
            self.next = [nd]
            while len(self.next):
                if node := self.next.pop(0).sync():
                    for i in node._jac_entry_funcs_:
                        if not i.trigger or isinstance(walker, i.trigger):
                            if i.func:
                                i.func(node, walker)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in walker._jac_entry_funcs_:
                        if not i.trigger or isinstance(node, i.trigger):
                            if i.func:
                                i.func(walker, node)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in walker._jac_exit_funcs_:
                        if not i.trigger or isinstance(node, i.trigger):
                            if i.func:
                                i.func(walker, node)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
                    for i in node._jac_exit_funcs_:
                        if not i.trigger or isinstance(walker, i.trigger):
                            if i.func:
                                i.func(node, walker)
                            else:
                                raise ValueError(f"No function {i.name} to call.")
                        if self.state.disengaged:
                            return walker
            self.ignores = []
            return walker
        raise Exception(f"Invalid Reference {self.ref_id}")


class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: list[DSFunc]
    _jac_exit_funcs_: list[DSFunc]
    __jac_classes__: dict[str, type[Architype]]
    __jac_hintings__: dict[str, type]

    def __init__(self, __jac__: Optional[Anchor] = None) -> None:
        """Create default architype."""
        if not __jac__:
            __jac__ = Anchor(architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, Architype):
            return super().__eq__(other)
        elif isinstance(other, Anchor):
            return self.__jac__ == other

        return False

    def __hash__(self) -> int:
        """Override hash for architype."""
        return self.__jac__.__hash__()

    def __repr__(self) -> str:
        """Override repr for architype."""
        return f"{self.__class__.__name__}"

    @classmethod
    def __set_classes__(cls) -> dict[str, Any]:
        """Initialize Jac Classes."""
        jac_classes = {}
        for sub in cls.__subclasses__():
            sub.__jac_hintings__ = get_type_hints(sub)
            jac_classes[sub.__name__] = sub
        cls.__jac_classes__ = jac_classes

        return jac_classes

    @classmethod
    def __get_class__(cls: TA, name: str) -> TA:
        """Build class map from subclasses."""
        jac_classes: dict[str, Any] | None = getattr(cls, "__jac_classes__", None)
        if not jac_classes or not (jac_class := jac_classes.get(name)):
            jac_classes = cls.__set_classes__()
            jac_class = jac_classes.get(name, cls)

        return jac_class


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    __jac__: NodeAnchor

    def __init__(self, __jac__: Optional[NodeAnchor] = None) -> None:
        """Create node architype."""
        if not __jac__:
            __jac__ = NodeAnchor(name=self.__class__.__name__, architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    __jac__: EdgeAnchor

    def __init__(self, __jac__: Optional[EdgeAnchor] = None) -> None:
        """Create edge architype."""
        if not __jac__:
            __jac__ = EdgeAnchor(name=self.__class__.__name__, architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    __jac__: WalkerAnchor

    def __init__(self, __jac__: Optional[WalkerAnchor] = None) -> None:
        """Create walker architype."""
        if not __jac__:
            __jac__ = WalkerAnchor(name=self.__class__.__name__, architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []

    def __init__(self, __jac__: Optional[EdgeAnchor] = None) -> None:
        """Create walker architype."""
        if not __jac__:
            __jac__ = EdgeAnchor(architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []
    reachable_nodes: list[NodeArchitype] = []
    connections: set[tuple[NodeArchitype, NodeArchitype, EdgeArchitype]] = set()

    def __init__(self, __jac__: Optional[NodeAnchor] = None) -> None:
        """Create walker architype."""
        if not __jac__:
            __jac__ = NodeAnchor(architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__

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
