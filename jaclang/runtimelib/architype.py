"""Core constructs for Jac Language."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum, IntEnum
from json import JSONEncoder, dumps
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
    get_args,
    get_origin,
    get_type_hints,
)
from uuid import UUID, uuid4

from jaclang.compiler.constant import EdgeDir, T
from jaclang.runtimelib.utils import collect_node_connections

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
TA = TypeVar("TA", bound="Architype")


def to_dataclass(cls: type[T], data: dict[str, Any], **kwargs: object) -> T:
    """Parse dict to dataclass."""
    hintings = get_type_hints(cls)
    for attr in fields(cls):  # type: ignore[arg-type]
        if target := data.get(attr.name):
            hint = hintings[attr.name]
            if is_dataclass(hint):
                data[attr.name] = to_dataclass(hint, target)
            else:
                origin = get_origin(hint)
                if origin == dict and isinstance(target, dict):
                    if is_dataclass(inner_cls := get_args(hint)[-1]):
                        for key, value in target.items():
                            target[key] = to_dataclass(inner_cls, value)
                elif (
                    origin == list
                    and isinstance(target, list)
                    and is_dataclass(inner_cls := get_args(hint)[-1])
                ):
                    for key, value in enumerate(target):
                        target[key] = to_dataclass(inner_cls, value)
    return cls(**data, **kwargs)


class UUIDEncoder(JSONEncoder):
    """UUID JSON Handler."""

    def default(self, obj: object) -> Any:  # noqa: ANN401
        """Override default handler."""
        if isinstance(obj, UUID):
            return obj.hex
        return super().default(obj)


class AnchorType(Enum):
    """Enum For Anchor Types."""

    generic = "g"
    node = "n"
    edge = "e"
    walker = "w"


class AccessLevel(IntEnum):
    """Access level enum."""

    NO_ACCESS = -1
    READ = 0
    CONNECT = 1
    WRITE = 2

    @staticmethod
    def cast(val: int | str | AccessLevel) -> AccessLevel:
        """Cast access level."""
        match val:
            case int():
                return AccessLevel(val)
            case str():
                return AccessLevel[val]
            case _:
                return val


@dataclass
class Access:
    """Access Structure."""

    whitelist: bool = True  # whitelist or blacklist
    anchors: dict[str, AccessLevel] = field(default_factory=dict)

    def check(
        self, anchor: str
    ) -> tuple[bool, AccessLevel]:  # whitelist or blacklist, has_read_access, level
        """Validate access."""
        if self.whitelist:
            return self.whitelist, self.anchors.get(anchor, AccessLevel.NO_ACCESS)
        else:
            return self.whitelist, self.anchors.get(anchor, AccessLevel.WRITE)

    def serialize(self) -> dict[str, object]:
        """Serialize Access."""
        return {
            "whitelist": self.whitelist,
            "anchors": {key: val.name for key, val in self.anchors.items()},
        }

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Access:
        """Deserialize Access."""
        anchors = cast(dict[str, str], data.get("anchors"))
        return Access(
            whitelist=bool(data.get("whitelist")),
            anchors={key: AccessLevel[val] for key, val in anchors.items()},
        )


@dataclass
class Permission:
    """Anchor Access Handler."""

    all: AccessLevel = AccessLevel.NO_ACCESS
    roots: Access = field(default_factory=Access)

    def serialize(self) -> dict[str, object]:
        """Serialize Permission."""
        return {"all": self.all.name, "roots": self.roots.serialize()}

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Permission:
        """Deserialize Permission."""
        return Permission(
            all=AccessLevel[data.get("all", AccessLevel.NO_ACCESS.name)],
            roots=Access.deserialize(data.get("roots", {})),
        )


@dataclass
class AnchorState:
    """Anchor state handler."""

    # None == do nothing
    # False == to be deleted
    # True == already deleted
    deleted: bool | None = None
    connected: bool = False
    current_access_level: AccessLevel = AccessLevel.NO_ACCESS
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
        """Return Anchor instance if valid."""
        if matched := GENERIC_ID_REGEX.search(ref_id):
            anchor: type = Anchor
            match AnchorType(matched.group(1)):
                case AnchorType.node:
                    anchor = NodeAnchor
                case AnchorType.edge:
                    anchor = EdgeAnchor
                case AnchorType.walker:
                    anchor = WalkerAnchor
                case _:
                    pass
            return anchor(name=matched.group(2), id=UUID(matched.group(3)))
        return None

    def whitelist_roots(self, whitelist: bool = True) -> None:
        """Toggle root whitelist/blacklist."""
        if whitelist != self.access.roots.whitelist:
            self.access.roots.whitelist = whitelist

    def allow_root(
        self, root: Anchor, level: AccessLevel | int | str = AccessLevel.READ
    ) -> None:
        """Allow all access from target root graph to current Architype."""
        level = AccessLevel.cast(level)
        access = self.access.roots
        if access.whitelist:
            if (ref_id := root.ref_id) and level != access.anchors.get(
                ref_id, AccessLevel.NO_ACCESS
            ):
                access.anchors[ref_id] = level
        else:
            self.disallow_root(root, level)

    def disallow_root(
        self, root: Anchor, level: AccessLevel | int | str = AccessLevel.READ
    ) -> None:
        """Disallow all access from target root graph to current Architype."""
        level = AccessLevel.cast(level)
        access = self.access.roots
        if access.whitelist:
            access.anchors.pop(root.ref_id, None)
        else:
            self.allow_root(root, level)

    def unrestrict(self, level: AccessLevel | int | str = AccessLevel.READ) -> None:
        """Allow everyone to access current Architype."""
        level = AccessLevel.cast(level)
        if level != self.access.all:
            self.access.all = level

    def restrict(self) -> None:
        """Disallow others to access current Architype."""
        if self.access.all > AccessLevel.NO_ACCESS:
            self.access.all = AccessLevel.NO_ACCESS

    def _save(self) -> None:
        """Save Anchor."""
        raise NotImplementedError("_save must be implemented in subclasses")

    def save(self) -> None:
        """Save Anchor."""
        if self.architype:
            if self.state.deleted is False:
                self.state.deleted = True
                self._destroy()
            elif not self.state.connected:
                self.state.connected = True
                self.sync_hash()
                self._save()
            elif (
                self.state.current_access_level > AccessLevel.READ
                and self.state.hash != (_hash := self.data_hash())
            ):
                self.state.hash = _hash
                self._save()

    def _destroy(self) -> None:
        """Destroy Anchor."""
        from .context import ExecutionContext

        ExecutionContext.get_datasource().remove(self, from_db=True)

    def destroy(self) -> None:
        """Destroy Anchor."""
        if (
            self.architype
            and self.state.current_access_level > AccessLevel.CONNECT
            and self.state.deleted is None
        ):
            from .context import ExecutionContext

            ctx_src = ExecutionContext.get_datasource()

            self.state.deleted = False
            ctx_src.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[Architype]:
        """Retrieve the Architype from db and return."""
        if self.state.deleted is not None:
            return None

        if architype := self.architype:
            if (node or self).has_read_access(self):
                return architype
            return None

        from .context import ExecutionContext

        ctx_src = ExecutionContext.get_datasource()
        anchor = ctx_src.find_one(self.id)

        if anchor and (node or self).has_read_access(anchor):
            self.__dict__.update(anchor.__dict__)

        return self.architype

    def allocate(self) -> None:
        """Allocate hashes and memory."""
        from .context import ExecutionContext

        ctx = ExecutionContext.get()
        if self.root is None and not isinstance(self.architype, Root):
            self.root = ctx.root.id
        ctx.datasource.set(self)

    def has_read_access(self, to: Anchor) -> bool:
        """Read Access Validation."""
        return self.access_level(to) > AccessLevel.NO_ACCESS

    def has_connect_access(self, to: Anchor) -> bool:
        """Write Access Validation."""
        return self.access_level(to) > AccessLevel.READ

    def has_write_access(self, to: Anchor) -> bool:
        """Write Access Validation."""
        return self.access_level(to) > AccessLevel.CONNECT

    def access_level(self, to: "Anchor") -> AccessLevel:
        """Access validation."""
        from .context import ExecutionContext

        ctx = ExecutionContext.get()
        jroot = ctx.root
        to.state.current_access_level = AccessLevel.NO_ACCESS

        # if current root is system_root
        # if current root id is equal to target anchor's root id
        # if current root is the target anchor
        if jroot == ctx.system_root or jroot.id == to.root or jroot == to:
            to.state.current_access_level = AccessLevel.WRITE
            return to.state.current_access_level

        # if target anchor have set access.all
        if (to_access := to.access).all > AccessLevel.NO_ACCESS:
            to.state.current_access_level = to_access.all

        # if target anchor's root have set allowed roots
        # if current root is allowed to the whole graph of target anchor's root
        if to.root and (to_root := ctx.datasource.find_one(to.root)):
            if to_root.access.all > to.state.current_access_level:
                to.state.current_access_level = to_root.access.all

            whitelist, level = to_root.access.roots.check(jroot.ref_id)
            if not whitelist:
                if level < AccessLevel.READ:
                    to.state.current_access_level = AccessLevel.NO_ACCESS
                    return to.state.current_access_level
                elif level < to.state.current_access_level:
                    level = to.state.current_access_level
            elif (
                whitelist
                and level > AccessLevel.NO_ACCESS
                and to.state.current_access_level == AccessLevel.NO_ACCESS
            ):
                to.state.current_access_level = level

        # if target anchor have set allowed roots
        # if current root is allowed to target anchor
        whitelist, level = to_access.roots.check(jroot.ref_id)
        if not whitelist:
            if level < AccessLevel.READ:
                to.state.current_access_level = AccessLevel.NO_ACCESS
                return to.state.current_access_level
            elif level < to.state.current_access_level:
                level = to.state.current_access_level
        elif (
            whitelist
            and level > AccessLevel.NO_ACCESS
            and to.state.current_access_level == AccessLevel.NO_ACCESS
        ):
            to.state.current_access_level = level

        return to.state.current_access_level

    def serialize(self) -> dict[str, object]:
        """Serialize Anchor."""
        return {
            "type": self.type.value,
            "name": self.name,
            "id": self.id,
            "root": self.root,
            "access": self.access.serialize(),
            "architype": (
                asdict(self.architype)
                if is_dataclass(self.architype) and not isinstance(self.architype, type)
                else {}
            ),
        }

    def data_hash(self) -> int:
        """Get current serialization hash."""
        return hash(dumps(self.serialize(), cls=UUIDEncoder))

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

        return False


@dataclass(eq=False)
class NodeAnchor(Anchor):
    """Node Anchor."""

    type: ClassVar[AnchorType] = AnchorType.node
    architype: Optional[NodeArchitype] = None
    edges: list[EdgeAnchor] = field(default_factory=list)

    @classmethod
    def ref(cls, ref_id: str) -> Optional[NodeAnchor]:
        """Return NodeAnchor instance if valid."""
        if match := NODE_ID_REGEX.search(ref_id):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        ctx_src = ExecutionContext.get_datasource()

        for edge in self.edges:
            edge.save()

        ctx_src.sync(self)

    def destroy(self) -> None:
        """Delete Anchor."""
        if (
            self.architype
            and self.state.current_access_level > AccessLevel.CONNECT
            and self.state.deleted is None
        ):
            from .context import ExecutionContext

            ctx_src = ExecutionContext.get_datasource()

            self.state.deleted = False
            for edge in self.edges:
                edge.destroy()
            ctx_src.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[NodeArchitype]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[NodeArchitype], super().sync(node))

    def connect_node(self, node: NodeAnchor, edge: EdgeAnchor) -> None:
        """Connect a node with given edge."""
        edge.attach(self, node)

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
                and (src_arch := source.sync())
                and (trg_arch := target.sync())
            ):
                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and (not target_cls or trg_arch.__class__ in target_cls)
                    and source.has_read_access(target)
                ):
                    ret_edges.append(architype)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
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
                and (src_arch := source.sync())
                and (trg_arch := target.sync())
            ):
                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and (not target_cls or trg_arch.__class__ in target_cls)
                    and source.has_read_access(target)
                ):
                    ret_edges.append(trg_arch)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
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
        """Return EdgeAnchor instance if valid."""
        if match := EDGE_ID_REGEX.search(ref_id):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        ctx_src = ExecutionContext.get_datasource()

        if source := self.source:
            source.save()

        if target := self.target:
            target.save()

        ctx_src.sync(self)

    def destroy(self) -> None:
        """Delete Anchor."""
        if (
            self.architype
            and self.state.current_access_level > AccessLevel.CONNECT
            and self.state.deleted is None
        ):
            from .context import ExecutionContext

            ctx_src = ExecutionContext.get_datasource()

            self.state.deleted = False
            self.detach()
            ctx_src.remove(self)

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
            "is_undirected": self.is_undirected,
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
        """Return WalkerAnchor instance if valid."""
        if ref_id and (match := WALKER_ID_REGEX.search(ref_id)):
            return cls(
                name=match.group(1),
                id=UUID(match.group(2)),
            )
        return None

    def _save(self) -> None:
        from .context import ExecutionContext

        ExecutionContext.get_datasource().sync(self)

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
    def __get_class__(cls: type[TA], name: str) -> type[TA]:
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


@dataclass(eq=False)
class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_: ClassVar[list[DSFunc]] = []  # type: ignore[misc]
    _jac_exit_funcs_: ClassVar[list[DSFunc]] = []  # type: ignore[misc]

    def __init__(self, __jac__: Optional[EdgeAnchor] = None) -> None:
        """Create walker architype."""
        if not __jac__:
            __jac__ = EdgeAnchor(architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


@dataclass(eq=False)
class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_: ClassVar[list[DSFunc]] = []  # type: ignore[misc]
    _jac_exit_funcs_: ClassVar[list[DSFunc]] = []  # type: ignore[misc]

    def __init__(self, __jac__: Optional[NodeAnchor] = None) -> None:
        """Create walker architype."""
        if not __jac__:
            __jac__ = NodeAnchor(architype=self)
            __jac__.allocate()
        self.__jac__ = __jac__


@dataclass(eq=False)
class DSFunc:
    """Data Spatial Function."""

    name: str
    trigger: type | UnionType | tuple[type | UnionType, ...] | None
    func: Callable[[Any, Any], Any] | None = None

    def resolve(self, cls: type) -> None:
        """Resolve the function."""
        self.func = getattr(cls, self.name)
