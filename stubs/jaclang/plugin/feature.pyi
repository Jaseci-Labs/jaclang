import types
from _typeshed import Incomplete
from jaclang.compiler.constant import EdgeDir as EdgeDir
from jaclang.plugin.default import (
    Architype as Architype,
    EdgeArchitype as EdgeArchitype,
    JacFeatureDefaults as JacFeatureDefaults,
    NodeArchitype as NodeArchitype,
    Root as Root,
    T as T,
    WalkerArchitype as WalkerArchitype,
)
from jaclang.plugin.spec import DSFunc as DSFunc, JacFeatureSpec as JacFeatureSpec
from typing import Any, Callable, Optional, Type, TypeAlias, Union

from jaclang.compiler.absyntree import Module

class JacFeature:
    pm: Incomplete
    import abc
    from jaclang.plugin.spec import DSFunc
    from jaclang.compiler.constant import EdgeDir

    RootType: TypeAlias = Root
    @staticmethod
    def make_obj(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_node(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_edge(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_walker(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def jac_import(
        target: str,
        base_path: str,
        absorb: bool = False,
        cachable: bool = True,
        mdl_alias: Optional[str] = None,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module | str] = None,
        lng: Optional[str] = None,
        items: Optional[dict[str, Union[str, bool]]] = None,
    ) -> Optional[types.ModuleType]: ...
    @staticmethod
    def create_test(test_fun: Callable) -> Callable: ...
    @staticmethod
    def run_test(filename: str) -> None: ...
    @staticmethod
    def elvis(op1: Optional[T], op2: T) -> T: ...
    @staticmethod
    def has_instance_default(gen_func: Callable[[], T]) -> T: ...
    @staticmethod
    def spawn_call(op1: Architype, op2: Architype) -> WalkerArchitype: ...
    @staticmethod
    def report(expr: Any) -> Any: ...
    @staticmethod
    def ignore(
        walker: WalkerArchitype,
        expr: (
            list[NodeArchitype | EdgeArchitype]
            | list[NodeArchitype]
            | list[EdgeArchitype]
            | NodeArchitype
            | EdgeArchitype
        ),
    ) -> bool: ...
    @staticmethod
    def visit_node(
        walker: WalkerArchitype,
        expr: (
            list[NodeArchitype | EdgeArchitype]
            | list[NodeArchitype]
            | list[EdgeArchitype]
            | NodeArchitype
            | EdgeArchitype
        ),
    ) -> bool: ...
    @staticmethod
    def disengage(walker: WalkerArchitype) -> bool: ...
    @staticmethod
    def edge_ref(
        node_obj: NodeArchitype | list[NodeArchitype],
        target_obj: Optional[NodeArchitype | list[NodeArchitype]],
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        edges_only: bool = False,
    ) -> list[NodeArchitype] | list[EdgeArchitype]: ...
    @staticmethod
    def connect(
        left: NodeArchitype | list[NodeArchitype],
        right: NodeArchitype | list[NodeArchitype],
        edge_spec: Callable[[], EdgeArchitype],
        edges_only: bool = False,
    ) -> list[NodeArchitype] | list[EdgeArchitype]: ...
    @staticmethod
    def disconnect(
        left: NodeArchitype | list[NodeArchitype],
        right: NodeArchitype | list[NodeArchitype],
        dir: EdgeDir,
        filter_type: Optional[type],
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
    ) -> bool: ...
    @staticmethod
    def assign_compr(
        target: list[T], attr_val: tuple[tuple[str], tuple[Any]]
    ) -> list[T]: ...
    @staticmethod
    def get_root() -> Root: ...
    @staticmethod
    def get_root_type() -> Type[Root]: ...
    @staticmethod
    def build_edge(
        is_undirected: bool,
        conn_type: Optional[Type[EdgeArchitype] | EdgeArchitype],
        conn_assign: Optional[tuple[tuple, tuple]],
    ) -> Callable[[], EdgeArchitype]: ...

class JacBuiltin:
    @staticmethod
    def dotgen(node: NodeArchitype, radius: int = 0) -> str: ...
