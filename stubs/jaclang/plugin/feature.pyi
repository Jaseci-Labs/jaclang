import types
from _typeshed import Incomplete
from jaclang.compiler.absyntree import Module as Module
from jaclang.compiler.constant import EdgeDir as EdgeDir
from jaclang.core.construct import (
    Architype as Architype,
    EdgeArchitype as EdgeArchitype,
    NodeArchitype as NodeArchitype,
    Root as Root,
    WalkerArchitype as WalkerArchitype,
)
from jaclang.core.memory import Memory as Memory
from jaclang.plugin.default import ExecutionContext as ExecutionContext
from jaclang.plugin.spec import (
    DSFunc as DSFunc,
    JacBuiltin as JacBuiltin,
    JacCmdSpec as JacCmdSpec,
    JacFeatureSpec as JacFeatureSpec,
    T as T,
)
from typing import Any, Callable, Optional, Type, Union

pm: Incomplete

class JacFeature:
    @staticmethod
    def context(session: str = "") -> ExecutionContext: ...
    @staticmethod
    def reset_context() -> None: ...
    @staticmethod
    def memory_hook() -> Memory | None: ...
    @staticmethod
    def make_architype(
        cls, arch_base: Type[Architype], on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Type[Architype]: ...
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
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = "jac",
        items: Optional[dict[str, Union[str, bool]]] = None,
    ) -> Optional[types.ModuleType]: ...
    @staticmethod
    def create_test(test_fun: Callable) -> Callable: ...
    @staticmethod
    def run_test(
        filepath: str,
        filter: Optional[str] = None,
        xit: bool = False,
        maxfail: Optional[int] = None,
        directory: Optional[str] = None,
        verbose: bool = False,
    ) -> bool: ...
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
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool: ...
    @staticmethod
    def visit_node(
        walker: WalkerArchitype,
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
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
        conn_type: Optional[Type[EdgeArchitype]],
        conn_assign: Optional[tuple[tuple, tuple]],
    ) -> Callable[[], EdgeArchitype]: ...
    @staticmethod
    def get_semstr_type(
        file_loc: str, scope: str, attr: str, return_semstr: bool
    ) -> Optional[str]: ...
    @staticmethod
    def obj_scope(file_loc: str, attr: str) -> str: ...
    @staticmethod
    def get_sem_type(file_loc: str, attr: str) -> tuple[str | None, str | None]: ...
    @staticmethod
    def with_llm(
        file_loc: str,
        model: Any,
        model_params: dict[str, Any],
        scope: str,
        incl_info: list[tuple[str, str]],
        excl_info: list[tuple[str, str]],
        inputs: list[tuple[str, str, str, Any]],
        outputs: tuple,
        action: str,
    ) -> Any: ...

class JacCmd:
    @staticmethod
    def create_cmd() -> None: ...
