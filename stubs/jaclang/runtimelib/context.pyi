import unittest
from .architype import NodeAnchor as NodeAnchor, Root as Root
from .machine import JacMachine as JacMachine, JacProgram as JacProgram
from .memory import ShelfStorage as ShelfStorage
from _typeshed import Incomplete
from typing import Any, Callable

EXECUTION_CONTEXT: Incomplete
SUPER_ROOT_UUID: str

class ExecutionContext:
    jac_machine: JacMachine
    datasource: ShelfStorage
    reports: list[Any]
    system_root: NodeAnchor
    root: NodeAnchor
    entry: NodeAnchor
    def generate_system_root(self) -> NodeAnchor: ...
    def load(
        self, anchor_id: str | None, default: NodeAnchor | Callable[[], NodeAnchor]
    ) -> NodeAnchor: ...
    def close(self) -> None: ...
    @staticmethod
    def create(
        base_path: str = "",
        session: str | None = None,
        root: str | None = None,
        entry: str | None = None,
    ) -> ExecutionContext: ...
    @staticmethod
    def get() -> ExecutionContext: ...

class JacTestResult(unittest.TextTestResult):
    failures_count: Incomplete
    max_failures: Incomplete
    def __init__(
        self, stream, descriptions, verbosity: int, max_failures: int | None = None
    ) -> None: ...
    def addFailure(self, test, err) -> None: ...
    shouldStop: bool
    def stop(self) -> None: ...

class JacTextTestRunner(unittest.TextTestRunner):
    max_failures: Incomplete
    def __init__(self, max_failures: int | None = None, **kwargs) -> None: ...

class JacTestCheck:
    test_case: Incomplete
    test_suite: Incomplete
    breaker: bool
    failcount: int
    @staticmethod
    def reset() -> None: ...
    @staticmethod
    def run_test(xit: bool, maxfail: int | None, verbose: bool) -> None: ...
    @staticmethod
    def add_test(test_fun: Callable) -> None: ...
    def __getattr__(self, name: str) -> object: ...
