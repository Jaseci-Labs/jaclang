"""Core constructs for Jac Language."""

from __future__ import annotations

import types
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING, Union
from uuid import UUID, uuid4

from jaclang.compiler.constant import EdgeDir
from jaclang.core.utils import collect_node_connections

if TYPE_CHECKING:
    from jaclang.plugin.feature import JacFeature as Jac


class AnchorType(Enum):
    """Enum For Graph Types."""

    node = "n"
    edge = "e"


@dataclass
class Anchor:
    """DocAnchor for Mongodb Referencing."""

    type: AnchorType
    name: str = ""
    id: ObjectId = field(default_factory=ObjectId)
    root: Optional[ObjectId] = None
    access: DocAccess = field(default_factory=DocAccess)
    connected: bool = False
    arch: Optional[Architype] = None

    # 0 == don't have access
    # 1 == with read access
    # 2 == with write access
    current_access_level: Optional[int] = None

    @property
    def ref_id(self) -> str:
        """Return id in reference type."""
        return f"{self.type.value}:{self.name}:{self.id}"

    @property
    def _set(self) -> dict:
        if "$set" not in self.changes:
            self.changes["$set"] = {}
        return self.changes["$set"]

    def _add_to_set(
        self, field: str, obj: Union["DocAnchor[DA]", ObjectId], remove: bool = False
    ) -> None:
        if "$addToSet" not in self.changes:
            self.changes["$addToSet"] = {}

        if field not in (add_to_set := self.changes["$addToSet"]):
            add_to_set[field] = {"$each": set()}

        ops: set = add_to_set[field]["$each"]

        if remove:
            if obj in ops:
                ops.remove(obj)
        else:
            ops.add(obj)
            self._pull(field, obj, True)

    def _pull(
        self, field: str, obj: Union["DocAnchor[DA]", ObjectId], remove: bool = False
    ) -> None:
        if "$pull" not in self.changes:
            self.changes["$pull"] = {}

        if field not in (pull := self.changes["$pull"]):
            pull[field] = {"$in": set()}

        ops: set = pull[field]["$in"]

        if remove:
            if obj in ops:
                ops.remove(obj)
        else:
            ops.add(obj)
            self._add_to_set(field, obj, True)

    def connect_edge(self, doc_anc: "DocAnchor[DA]", rollback: bool = False) -> None:
        """Push update that there's newly added edge."""
        if not rollback:
            self._add_to_set("edge", doc_anc)
        else:
            self._pull("edge", doc_anc, True)

    def disconnect_edge(self, doc_anc: "DocAnchor[DA]") -> None:
        """Push update that there's edge that has been removed."""
        self._pull("edge", doc_anc)

    def allow_node(self, node_id: ObjectId, write: bool = False) -> None:
        """Allow target node to access current Architype."""
        w = 1 if write else 0
        if node_id not in (nodes := self.access.nodes[w]):
            nodes.add(node_id)
            self._add_to_set(f"access.nodes.{w}", node_id)

    def disallow_node(self, node_id: ObjectId) -> None:
        """Remove target node access from current Architype."""
        for w in range(0, 2):
            if node_id in (nodes := self.access.nodes[w]):
                nodes.remove(node_id)
                self._pull(f"access.nodes.{w}", node_id)

    def allow_root(self, root_id: ObjectId, write: bool = False) -> None:
        """Allow all access from target root graph to current Architype."""
        w = 1 if write else 0
        if root_id not in (roots := self.access.roots[w]):
            roots.add(root_id)
            self._add_to_set(f"access.roots.{w}", root_id)

    def disallow_root(self, root_id: ObjectId) -> None:
        """Disallow all access from target root graph to current Architype."""
        for w in range(0, 2):
            if root_id in (roots := self.access.roots[w]):
                roots.remove(root_id)
                self._pull(f"access.roots.{w}", root_id)

    def unrestrict(self, write: bool = False) -> None:
        """Allow everyone to access current Architype."""
        w = 2 if write else 1
        if w > self.access.all:
            self.access.all = w
            self._set.update({"access.all": w})

    def restrict(self) -> None:
        """Disallow others to access current Architype."""
        if self.access.all:
            self.access.all = 0
            self._set.update({"access.all": 0})

    def class_ref(self) -> Type[DA]:
        """Return generated class equivalent for DocAnchor."""
        if self.type is JType.node:
            return JCLASS[self.type.value].get(self.name, NodeArchitype)
        return JCLASS[self.type.value].get(self.name, EdgeArchitype)

    def pull_changes(self) -> dict:
        """Return changes and clear current reference."""
        self.rollback_changes = deepcopy(self.changes)
        self.rollback_hashes = copy(self.hashes)

        changes = self.changes
        _set = changes.pop("$set", {})
        self.changes = {}  # renew reference

        if is_dataclass(self.arch) and not isinstance(self.arch, type):
            for key, val in asdict(self.arch).items():
                if (h := hash(dumps(val))) != self.hashes.get(key):
                    self.hashes[key] = h
                    _set[f"context.{key}"] = val

        if _set:
            changes["$set"] = _set

        return changes

    def rollback(self) -> None:
        """Rollback hashes so set update still available."""
        self.hashes = self.rollback_hashes
        self.changes = self.rollback_changes

    def build(self, **kwargs: Any) -> DA:  # noqa: ANN401
        """Return generated class instance equivalent for DocAnchor."""
        arch = self.arch = self.class_ref()(**kwargs)

        if isinstance(arch, DocArchitype):
            arch._jac_doc_ = self

        return arch

    def json(self) -> dict:
        """Return in dictionary type."""
        return {
            "_id": self.id,
            "name": self.name,
            "root": self.root,
            "access": self.access.json(),
        }

    @classmethod
    def ref(cls, ref_id: str) -> Optional["DocAnchor[DA]"]:
        """Return DocAnchor instance if ."""
        if ref_id and (match := TARGET_NODE_REGEX.search(ref_id)):
            return cls(
                type=JType(match.group(1)),
                name=match.group(2),
                id=ObjectId(match.group(3)),
            )
        return None

    def connect(self, node: Optional["NodeArchitype"] = None) -> Optional[DA]:
        """Sync Retrieve the Architype from db and return."""
        return get_event_loop().run_until_complete(self._connect(node))

    async def _connect(self, node: Optional["NodeArchitype"] = None) -> Optional[DA]:
        """Retrieve the Architype from db and return."""
        jctx: JacContext = JacContext.get_context()

        if obj := jctx.get(self.id):
            self.arch = obj
            return obj

        cls = self.class_ref()
        if (
            cls
            and (data := await cls.Collection.find_by_id(self.id))
            and isinstance(data, (NodeArchitype, EdgeArchitype))
            and (
                await jctx.root.is_allowed(data)
                or (node and await node.is_allowed(data))
            )
        ):
            self.arch = data
            jctx.set(data._jac_doc_.id, data)

        if isinstance(data, (NodeArchitype, EdgeArchitype)):
            return data
        return None

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, DocAnchor):
            return (
                self.type == other.type
                and self.name == other.name
                and self.id == other.id
            )
        elif isinstance(other, DocArchitype):
            return self == other._jac_doc_

        return False

    def __hash__(self) -> int:
        """Override hash implementation."""
        return hash(self.ref_id)

    def __deepcopy__(self, memo: dict) -> "DocAnchor[DA]":
        """Override deepcopy implementation."""
        memo[id(self)] = self
        return self


@dataclass(eq=False)
class ElementAnchor:
    """Element Anchor."""

    obj: Architype
    id: UUID = field(default_factory=uuid4)


@dataclass(eq=False)
class ObjectAnchor(ElementAnchor):
    """Object Anchor."""

    def spawn_call(self, walk: WalkerArchitype) -> WalkerArchitype:
        """Invoke data spatial call."""
        return walk._jac_.spawn_call(self.obj)


@dataclass(eq=False)
class NodeAnchor(ObjectAnchor):
    """Node Anchor."""

    obj: NodeArchitype
    edges: list[EdgeArchitype] = field(default_factory=lambda: [])

    def connect_node(self, nd: NodeArchitype, edg: EdgeArchitype) -> NodeArchitype:
        """Connect a node with given edge."""
        edg._jac_.attach(self.obj, nd)
        return self.obj

    def get_edges(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[EdgeArchitype]:
        """Get edges connected to this node."""
        edge_list: list[EdgeArchitype] = [*self.edges]
        ret_edges: list[EdgeArchitype] = []
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

    def edges_to_nodes(
        self,
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        target_obj: Optional[list[NodeArchitype]],
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        edge_list: list[EdgeArchitype] = [*self.edges]
        node_list: list[NodeArchitype] = []
        edge_list = filter_func(edge_list) if filter_func else edge_list
        for e in edge_list:
            if e._jac_.target and e._jac_.source:
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

    def gen_dot(self, dot_file: Optional[str] = None) -> str:
        """Generate Dot file for visualizing nodes and edges."""
        visited_nodes: set[NodeAnchor] = set()
        connections: set[tuple[NodeArchitype, NodeArchitype, str]] = set()
        unique_node_id_dict = {}

        collect_node_connections(self, visited_nodes, connections)
        dot_content = 'digraph {\nnode [style="filled", shape="ellipse", fillcolor="invis", fontcolor="black"];\n'
        for idx, i in enumerate([nodes_.obj for nodes_ in visited_nodes]):
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


@dataclass(eq=False)
class EdgeAnchor(ObjectAnchor):
    """Edge Anchor."""

    obj: EdgeArchitype
    source: Optional[NodeArchitype] = None
    target: Optional[NodeArchitype] = None
    is_undirected: bool = False

    def attach(
        self, src: NodeArchitype, trg: NodeArchitype, is_undirected: bool = False
    ) -> EdgeAnchor:
        """Attach edge to nodes."""
        self.source = src
        self.target = trg
        self.is_undirected = is_undirected
        src._jac_.edges.append(self.obj)
        trg._jac_.edges.append(self.obj)
        return self

    def detach(
        self, src: NodeArchitype, trg: NodeArchitype, is_undirected: bool = False
    ) -> None:
        """Detach edge from nodes."""
        self.is_undirected = is_undirected
        src._jac_.edges.remove(self.obj)
        trg._jac_.edges.remove(self.obj)
        self.source = None
        self.target = None
        del self

    def spawn_call(self, walk: WalkerArchitype) -> WalkerArchitype:
        """Invoke data spatial call."""
        if self.target:
            return walk._jac_.spawn_call(self.target)
        else:
            raise ValueError("Edge has no target.")


@dataclass(eq=False)
class WalkerAnchor(ObjectAnchor):
    """Walker Anchor."""

    obj: WalkerArchitype
    path: list[Architype] = field(default_factory=lambda: [])
    next: list[Architype] = field(default_factory=lambda: [])
    ignores: list[Architype] = field(default_factory=lambda: [])
    disengaged: bool = False

    def visit_node(
        self,
        nds: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
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
                    if i._jac_.target:
                        self.next.append(i._jac_.target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.next) > before_len

    def ignore_node(
        self,
        nds: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
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
                    if i._jac_.target:
                        self.ignores.append(i._jac_.target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.ignores) > before_len

    def disengage_now(self) -> None:
        """Disengage walker from traversal."""
        self.disengaged = True

    def spawn_call(self, nd: Architype) -> WalkerArchitype:
        """Invoke data spatial call."""
        self.path = []
        self.next = [nd]
        while len(self.next):
            nd = self.next.pop(0)
            for i in nd._jac_entry_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        i.func(nd, self.obj)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return self.obj
            for i in self.obj._jac_entry_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        i.func(self.obj, nd)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return self.obj
            for i in self.obj._jac_exit_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        i.func(self.obj, nd)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return self.obj
            for i in nd._jac_exit_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        i.func(nd, self.obj)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return self.obj
        self.ignores = []
        return self.obj


class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: list[DSFunc]
    _jac_exit_funcs_: list[DSFunc]

    def __init__(self) -> None:
        """Create default architype."""
        self._jac_: ObjectAnchor = ObjectAnchor(obj=self)

    def __hash__(self) -> int:
        return hash(self._jac_.id)

    def __eq__(self, other: Architype) -> bool:
        if isinstance(other, Architype):
            return self._jac_.id == other._jac_.id
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    _jac_: NodeAnchor

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_: NodeAnchor = NodeAnchor(obj=self)


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    _jac_: EdgeAnchor

    def __init__(self) -> None:
        """Create edge architype."""
        self._jac_: EdgeAnchor = EdgeAnchor(obj=self)


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    _jac_: WalkerAnchor

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_: WalkerAnchor = WalkerAnchor(obj=self)


class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []
    reachable_nodes: list[NodeArchitype] = []
    connections: set[tuple[NodeArchitype, NodeArchitype, EdgeArchitype]] = set()

    def reset(self) -> None:
        """Reset the root."""
        self.reachable_nodes = []
        self.connections = set()
        self._jac_.edges = []


class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []


@dataclass(eq=False)
class DSFunc:
    """Data Spatial Function."""

    name: str
    trigger: type | types.UnionType | tuple[type | types.UnionType, ...] | None
    func: Callable[[Any, Any], Any] | None = None

    def resolve(self, cls: type) -> None:
        """Resolve the function."""
        self.func = getattr(cls, self.name)


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

    def __getattr__(self, name: str) -> Union[bool, Any]:
        """Make convenient check.Equal(...) etc."""
        return getattr(JacTestCheck.test_case, name)
