"""Core constructs for Jac Language."""

from __future__ import annotations

import unittest
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from os import getenv
from pickle import dumps
from re import IGNORECASE, compile
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    TypedDict,
    Union,
    cast,
)
from uuid import UUID, uuid4

from jaclang.compiler.constant import EdgeDir
from jaclang.core.utils import collect_node_connections
from jaclang.plugin.spec import DSFunc


T = TypeVar("T")
GENERIC_ID_REGEX = compile(r"^(g|n|e|w):([^:]*):([a-f\d]{24})$", IGNORECASE)
NODE_ID_REGEX = compile(r"^n:([^:]*):([a-f\d]{24})$", IGNORECASE)
EDGE_ID_REGEX = compile(r"^e:([^:]*):([a-f\d]{24})$", IGNORECASE)
WALKER_ID_REGEX = compile(r"^w:([^:]*):([a-f\d]{24})$", IGNORECASE)
ENABLE_MANUAL_SAVE = getenv("ENABLE_MANUAL_SAVE") == "true"


class ObjectType(Enum):
    """Enum For Anchor Types."""

    generic = "g"
    node = "n"
    edge = "e"
    walker = "w"


@dataclass
class AnchorAccess(Generic[T]):
    """Anchor Access Handler."""

    all: int = 0
    nodes: tuple[set[T], set[T]] = field(default_factory=lambda: (set(), set()))
    roots: tuple[set[T], set[T]] = field(default_factory=lambda: (set(), set()))


@dataclass(eq=False)
class ObjectAnchor:
    """Object Anchor."""

    type: ObjectType = ObjectType.generic
    name: str = ""
    id: UUID = field(default_factory=uuid4)
    root: Optional[UUID] = None
    access: AnchorAccess[UUID] = field(default_factory=AnchorAccess[UUID])
    architype: Optional[Architype] = None
    connected: bool = False
    current_access_level: Optional[int] = None
    persistent: Optional[bool] = field(default=not ENABLE_MANUAL_SAVE)
    hash: int = 0

    def __post_init__(self) -> None:
        """Populate on memory."""
        self.hash = hash(dumps(self))
        ExecutionContext.get().datasource.set(self, True)

    @property
    def ref_id(self) -> str:
        """Return id in reference type."""
        return f"{self.type.value}:{self.name}:{self.id}"

    @classmethod
    def ref(cls, ref_id: str) -> Optional[ObjectAnchor]:
        """Return DocAnchor instance if ."""
        if ref_id and (match := GENERIC_ID_REGEX.search(ref_id)):
            return cls(
                type=ObjectType(match.group(1)),
                name=match.group(2),
                id=UUID(match.group(3)),
            )
        return None

    def save(self) -> None:
        """Save Anchor."""
        raise Exception(f"Invalid Reference {self.ref_id}")

    def destroy(self) -> None:
        """Save Anchor."""
        raise Exception(f"Invalid Reference {self.ref_id}")

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[ObjectAnchor]:
        """Retrieve the Architype from db and return."""
        if self.architype:
            return self

        jsrc = ExecutionContext.get().datasource
        anchor = jsrc.find_one(self.id)

        if anchor and (node or self).is_allowed(anchor):
            return anchor

        return None

    def unsync(self) -> ObjectAnchor:
        """Generate unlinked anchor."""
        return ObjectAnchor(self.type, self.name, self.id)

    def is_allowed(self, to: Union[ObjectAnchor, Architype]) -> bool:
        """Access validation."""
        jctx = ExecutionContext.get()
        jsrc = jctx.datasource
        jroot = jctx.root
        to = to._jac_ if isinstance(to, Architype) else to

        if jroot == ROOT or jroot == to.root:
            to.current_access_level = 1
            return True

        if (to_access := to.access).all:
            to.current_access_level = to_access.all - 1
            return True

        if jroot == self.root:
            for i in range(1, -1, -1):
                if self.id in to_access.nodes[i] or self.root in to_access.roots[i]:
                    to.current_access_level = i
                    return True

            if to.root and (to_root := jsrc.find_one(to.root)):
                to_root_access = to_root.access
                from_root_id = jroot.id
                for i in range(1, -1, -1):
                    if from_root_id in to_root_access.roots[i]:
                        to.current_access_level = i
                        return True

        to.current_access_level = None
        return False

    def __getstate__(self) -> dict[str, Any]:
        """Override getstate for pickle and shelve."""
        return self.__dict__.copy()

    def __setstate__(self, state: dict) -> None:
        """Override setstate for pickle and shelve."""
        self.__dict__.update(state)

    def __hash__(self) -> int:
        """Override hash for anchor."""
        return hash(self.ref_id)

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, ObjectAnchor):
            return (
                self.type == other.type
                and self.name == other.name
                and self.id == other.id
            )
        elif isinstance(other, Architype):
            return self == other._jac_

        return False


@dataclass(eq=False)
class NodeAnchor(ObjectAnchor):
    """Node Anchor."""

    type: ObjectType = ObjectType.node
    architype: Optional[NodeArchitype] = None
    edges: list[EdgeAnchor] = field(default_factory=list)

    @classmethod
    def ref(cls, ref_id: str) -> Optional[NodeAnchor]:
        """Return NodeAnchor instance if existing."""
        if ref_id and (match := NODE_ID_REGEX.search(ref_id)):
            return cls(
                name=match.group(2),
                id=UUID(match.group(3)),
            )
        return None

    def _save(self) -> None:
        jsrc = ExecutionContext.get().datasource

        for edge in self.edges:
            edge.save()

        jsrc.set(self)

    def save(self) -> None:
        """Save Anchor."""
        if self.architype:
            if self.connected:
                self.connected = True
                self._save()
            elif self.hash != (_hash := hash(dumps(self))):
                self.hash = _hash
                self._save()

    def destroy(self) -> None:
        """Delete Anchor."""
        if self.architype:
            jsrc = ExecutionContext.get().datasource
            for edge in self.edges:
                edge.destroy()

            jsrc.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[NodeAnchor]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[NodeAnchor], super().sync(node))

    def unsync(self) -> NodeAnchor:
        """Generate unlinked anchor."""
        return NodeAnchor(name=self.name, id=self.id)

    def connect_node(self, nd: NodeAnchor, edg: EdgeAnchor) -> None:
        """Connect a node with given edge."""
        edg.attach(self, nd)

    def get_edges(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[EdgeArchitype]:
        """Get edges connected to this node."""
        ret_edges: list[EdgeArchitype] = []
        for idx, anchor in enumerate(self.edges):
            if (_anchor := anchor.sync()) and _anchor is not anchor:
                self.edges[idx] = anchor = _anchor

            if (
                (architype := anchor.architype)
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
            ):
                if (_source := source.sync()) and _source is not source:
                    anchor.source = source = _source

                if (_target := target.sync()) and _target is not target:
                    anchor.target = target = _target

                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and (not target_obj or target.architype.__class__ in target_obj)
                    and source.is_allowed(target)
                ):
                    ret_edges.append(architype)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and (not target_obj or source.architype.__class__ in target_obj)
                    and target.is_allowed(source)
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
        for idx, anchor in enumerate(self.edges):
            if (_anchor := anchor.sync()) and _anchor is not anchor:
                self.edges[idx] = anchor = _anchor

            if (
                (architype := anchor.architype)
                and (source := anchor.source)
                and (target := anchor.target)
                and (not filter_func or filter_func([architype]))
            ):
                if (_source := source.sync()) and _source is not source:
                    anchor.source = source = _source

                if (_target := target.sync()) and _target is not target:
                    anchor.target = target = _target

                if (
                    dir in [EdgeDir.OUT, EdgeDir.ANY]
                    and self == source
                    and target.architype
                    and (not target_obj or target.architype.__class__ in target_obj)
                    and source.is_allowed(target)
                ):
                    ret_edges.append(target.architype)
                if (
                    dir in [EdgeDir.IN, EdgeDir.ANY]
                    and self == target
                    and source.architype
                    and (not target_obj or source.architype.__class__ in target_obj)
                    and target.is_allowed(source)
                ):
                    ret_edges.append(source.architype)
        return ret_edges

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

    def __getstate__(self) -> dict[str, Any]:
        """Override getstate for pickle and shelve."""
        state = self.__dict__.copy()
        state["edges"] = [edge.unsync() for edge in self.edges]
        return state


@dataclass(eq=False)
class EdgeAnchor(ObjectAnchor):
    """Edge Anchor."""

    type: ObjectType = ObjectType.edge
    architype: Optional[EdgeArchitype] = None
    source: Optional[NodeAnchor] = None
    target: Optional[NodeAnchor] = None
    is_undirected: bool = False

    @classmethod
    def ref(cls, ref_id: str) -> Optional[EdgeAnchor]:
        """Return EdgeAnchor instance if existing."""
        if ref_id and (match := EDGE_ID_REGEX.search(ref_id)):
            return cls(
                name=match.group(2),
                id=UUID(match.group(3)),
            )
        return None

    def _save(self) -> None:
        jsrc = ExecutionContext.get().datasource

        if source := self.source:
            source.save()

        if target := self.target:
            target.save()

        jsrc.set(self)

    def save(self) -> None:
        """Save Anchor."""
        if self.architype:
            if self.connected:
                self.connected = True
                self._save()
            elif self.hash != (_hash := hash(dumps(self))):
                self.hash = _hash
                self._save()

    def destroy(self) -> None:
        """Delete Anchor."""
        if self.architype:
            jsrc = ExecutionContext.get().datasource

            source = self.source
            target = self.target
            self.detach()

            if source:
                source.save()
            if target:
                target.save()

            jsrc.remove(self)

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[EdgeAnchor]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[EdgeAnchor], super().sync(node))

    def unsync(self) -> EdgeAnchor:
        """Generate unlinked anchor."""
        return EdgeAnchor(name=self.name, id=self.id)

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
            source.edges.remove(self)
        if target := self.target:
            target.edges.remove(self)

        self.source = None
        self.target = None

    def spawn_call(self, walk: WalkerAnchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if target := self.target:
            return walk.spawn_call(target)
        else:
            raise ValueError("Edge has no target.")

    def __getstate__(self) -> dict[str, Any]:
        """Override getstate for pickle and shelve."""
        state = self.__dict__.copy()
        if self.source:
            state["source"] = self.source.unsync()
        if self.target:
            state["target"] = self.target.unsync()
        return state


@dataclass(eq=False)
class WalkerAnchor(ObjectAnchor):
    """Walker Anchor."""

    type: ObjectType = ObjectType.walker
    architype: Optional[WalkerArchitype] = None
    path: list[Architype] = field(default_factory=list)
    next: list[Architype] = field(default_factory=list)
    ignores: list[Architype] = field(default_factory=list)
    disengaged: bool = False

    @classmethod
    def ref(cls, ref_id: str) -> Optional[WalkerAnchor]:
        """Return EdgeAnchor instance if existing."""
        if ref_id and (match := WALKER_ID_REGEX.search(ref_id)):
            return cls(
                name=match.group(2),
                id=UUID(match.group(3)),
            )
        return None

    def sync(self, node: Optional["NodeAnchor"] = None) -> Optional[WalkerAnchor]:
        """Retrieve the Architype from db and return."""
        return cast(Optional[WalkerAnchor], super().sync(node))

    def unsync(self) -> WalkerAnchor:
        """Generate unlinked anchor."""
        return WalkerAnchor(name=self.name, id=self.id)

    def visit_node(
        self,
        nds: (
            list[NodeArchitype | EdgeArchitype]
            | list[NodeArchitype]
            | list[EdgeArchitype]
            | NodeArchitype
            | EdgeArchitype
        ),
    ) -> bool:
        """Walker visits node."""
        nd_list: list[NodeArchitype | EdgeArchitype]
        if not isinstance(nds, list):
            nd_list = [nds]
        else:
            nd_list = list(nds)
        before_len = len(self.next)
        for i in nd_list:
            if i not in self.ignores:
                if isinstance(i, NodeArchitype):
                    self.next.append(i)
                elif isinstance(i, EdgeArchitype):
                    if (target := i._jac_.target) and (architype := target.architype):
                        self.next.append(architype)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.next) > before_len

    def ignore_node(
        self,
        nds: (
            list[NodeArchitype | EdgeArchitype]
            | list[NodeArchitype]
            | list[EdgeArchitype]
            | NodeArchitype
            | EdgeArchitype
        ),
    ) -> bool:
        """Walker ignores node."""
        nd_list: list[NodeArchitype | EdgeArchitype]
        if not isinstance(nds, list):
            nd_list = [nds]
        else:
            nd_list = list(nds)
        before_len = len(self.ignores)
        for i in nd_list:
            if i not in self.ignores:
                if isinstance(i, NodeArchitype):
                    self.ignores.append(i)
                elif isinstance(i, EdgeArchitype):
                    if (target := i._jac_.target) and (architype := target.architype):
                        self.ignores.append(architype)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.ignores) > before_len

    def disengage_now(self) -> None:
        """Disengage walker from traversal."""
        self.disengaged = True

    def spawn_call(self, nd: ObjectAnchor) -> WalkerArchitype:
        """Invoke data spatial call."""
        if (walker := self.architype) and (node := nd.architype):
            self.path = []
            self.next = [node]
            while len(self.next):
                node = self.next.pop(0)
                for i in node._jac_entry_funcs_:
                    if not i.trigger or isinstance(walker, i.trigger):
                        if i.func:
                            i.func(node, walker)
                        else:
                            raise ValueError(f"No function {i.name} to call.")
                    if self.disengaged:
                        return walker
                for i in walker._jac_entry_funcs_:
                    if not i.trigger or isinstance(node, i.trigger):
                        if i.func:
                            i.func(walker, node)
                        else:
                            raise ValueError(f"No function {i.name} to call.")
                    if self.disengaged:
                        return walker
                for i in walker._jac_exit_funcs_:
                    if not i.trigger or isinstance(node, i.trigger):
                        if i.func:
                            i.func(walker, node)
                        else:
                            raise ValueError(f"No function {i.name} to call.")
                    if self.disengaged:
                        return walker
                for i in node._jac_exit_funcs_:
                    if not i.trigger or isinstance(walker, i.trigger):
                        if i.func:
                            i.func(node, walker)
                        else:
                            raise ValueError(f"No function {i.name} to call.")
                    if self.disengaged:
                        return walker
            self.ignores = []
            return walker
        raise Exception(f"Invalid Reference {self.ref_id}")


class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: list[DSFunc]
    _jac_exit_funcs_: list[DSFunc]

    def __init__(self) -> None:
        """Create default architype."""
        self._jac_: ObjectAnchor = ObjectAnchor(architype=self)

    def __getstate__(self) -> dict[str, Any]:
        """Override getstate for pickle and shelve."""
        state = self.__dict__.copy()
        state["_jac_"] = self._jac_.unsync()
        return state

    def __setstate__(self, state: dict) -> None:
        """Override setstate for pickle and shelve."""
        self.__dict__.update(state)

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, Architype):
            return self._jac_.id == other._jac_.id
        elif isinstance(other, ObjectAnchor):
            return self._jac_ == other

        return False

    def __hash__(self) -> int:
        """Override hash for architype."""
        return self._jac_.__hash__()

    def __repr__(self) -> str:
        """Return string representation."""
        return self._jac_.ref_id


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    _jac_: NodeAnchor

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(
            name=self.__class__.__name__, architype=self
        )


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    _jac_: EdgeAnchor

    def __init__(self) -> None:
        """Create edge architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(
            name=self.__class__.__name__, architype=self
        )


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    _jac_: WalkerAnchor

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_: WalkerAnchor = WalkerAnchor(
            name=self.__class__.__name__, architype=self
        )


class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(architype=self)


class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []
    reachable_nodes: list[NodeArchitype] = []
    connections: set[tuple[NodeArchitype, NodeArchitype, EdgeArchitype]] = set()

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_: NodeAnchor = NodeAnchor(architype=self)

    def reset(self) -> None:
        """Reset the root."""
        self.reachable_nodes = []
        self.connections = set()
        self._jac_.edges = []


class ContextOptions(TypedDict, total=False):
    """Execution Context Options."""

    root: str
    entry: str


class ExecutionContext:
    """Execution Context."""

    def __init__(
        self,
        session: Optional[str] = "",
        root: Optional[str] = None,
        entry: Optional[str] = None,
    ) -> None:
        """Create JacContext."""
        from jaclang.plugin.memory import ShelfMemory

        self.datasource: ShelfMemory = ShelfMemory(session)
        self.reports: list[Any] = []
        self.root: NodeAnchor
        self.entry: NodeAnchor

        if (
            root
            and (rf := NodeAnchor.ref(root))
            and (ra := rf.sync())
            and isinstance(ra.architype, Root)
        ):
            self.root = ra
        else:
            self.root = ROOT

        if entry and (ef := NodeAnchor.ref(entry)) and (ea := ef.sync()):
            self.entry = ea
        else:
            self.entry = self.root

    def close(self) -> None:
        """Clean up context."""
        self.datasource.close()

    @staticmethod
    def get(
        session: str = "", options: Optional[ContextOptions] = None
    ) -> ExecutionContext:
        """Get or create execution context."""
        if not isinstance(ctx := EXECUTION_CONTEXT.get(None), ExecutionContext):
            EXECUTION_CONTEXT.set(ctx := ExecutionContext(session, **options or {}))
        return ctx


class JacTestResult(unittest.TextTestResult):
    """Jac test result class."""

    def __init__(
        self,
        stream,  # noqa
        descriptions,  # noqa
        verbosity: int,
        max_failures: Optional[int] = None,
    ) -> None:
        """Initialize FailFastTestResult object."""
        super().__init__(stream, descriptions, verbosity)  # noqa
        self.failures_count = JacTestCheck.failcount
        self.max_failures = max_failures

    def addFailure(self, test, err) -> None:  # noqa
        """Count failures and stop."""
        super().addFailure(test, err)
        self.failures_count += 1
        if self.max_failures is not None and self.failures_count >= self.max_failures:
            self.stop()

    def stop(self) -> None:
        """Stop the test execution."""
        self.shouldStop = True


class JacTextTestRunner(unittest.TextTestRunner):
    """Jac test runner class."""

    def __init__(self, max_failures: Optional[int] = None, **kwargs) -> None:  # noqa
        """Initialize JacTextTestRunner object."""
        self.max_failures = max_failures
        super().__init__(**kwargs)

    def _makeResult(self) -> JacTestResult:  # noqa
        """Override the method to return an instance of JacTestResult."""
        return JacTestResult(
            self.stream,
            self.descriptions,
            self.verbosity,
            max_failures=self.max_failures,
        )


class JacTestCheck:
    """Jac Testing and Checking."""

    test_case = unittest.TestCase()
    test_suite = unittest.TestSuite()
    breaker = False
    failcount = 0

    @staticmethod
    def reset() -> None:
        """Clear the test suite."""
        JacTestCheck.test_case = unittest.TestCase()
        JacTestCheck.test_suite = unittest.TestSuite()

    @staticmethod
    def run_test(xit: bool, maxfail: int | None, verbose: bool) -> None:
        """Run the test suite."""
        verb = 2 if verbose else 1
        runner = JacTextTestRunner(max_failures=maxfail, failfast=xit, verbosity=verb)
        result = runner.run(JacTestCheck.test_suite)
        if result.wasSuccessful():
            print("Passed successfully.")
        else:
            fails = len(result.failures)
            JacTestCheck.failcount += fails
            JacTestCheck.breaker = (
                (JacTestCheck.failcount >= maxfail) if maxfail else True
            )

    @staticmethod
    def add_test(test_fun: Callable) -> None:
        """Create a new test."""
        JacTestCheck.test_suite.addTest(unittest.FunctionTestCase(test_fun))

    def __getattr__(self, name: str) -> object:
        """Make convenient check.Equal(...) etc."""
        return getattr(JacTestCheck.test_case, name)


EXECUTION_CONTEXT = ContextVar[ExecutionContext]("ExecutionContext")
ROOT = NodeAnchor(id=UUID(int=0))
ROOT_ARCH = ROOT.architype = object.__new__(Root)
ROOT_ARCH._jac_ = ROOT
