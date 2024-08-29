"""Core constructs for Jac Language."""

from __future__ import annotations

import unittest
from contextvars import ContextVar
from typing import Any, Callable, Optional, cast
from uuid import UUID

from .architype import AccessLevel, NodeAnchor, Root
from .memory import Memory, ShelfStorage


EXECUTION_CONTEXT = ContextVar[Optional["ExecutionContext"]]("ExecutionContext")

SUPER_ROOT_UUID = UUID("00000000-0000-0000-0000-000000000000")
SUPER_ROOT_ARCHITYPE = object.__new__(Root)
SUPER_ROOT_ANCHOR = NodeAnchor(
    id=SUPER_ROOT_UUID, architype=SUPER_ROOT_ARCHITYPE, persistent=False, edges=[]
)
SUPER_ROOT_ARCHITYPE.__jac__ = SUPER_ROOT_ANCHOR


class ExecutionContext:
    """Execution Context."""

    mem: Memory
    reports: list[Any]
    system_root: NodeAnchor
    root: NodeAnchor
    __entry__: NodeAnchor | str | None

    def generate_system_root(self) -> NodeAnchor:
        """Generate default system root."""
        architype = object.__new__(Root)
        anchor = NodeAnchor(
            id=UUID(SUPER_ROOT_UUID), architype=architype, persistent=True, edges=[]
        )
        architype.__jac__ = anchor
        self.mem.set(anchor.id, anchor)
        return anchor

    @property
    def entry(self) -> NodeAnchor:
        """Get entry lazy load."""
        match self.__entry__:
            case NodeAnchor():
                pass
            case str():
                self.__entry__ = self.init_anchor(self.__entry__, self.root)
            case _:
                self.__entry__ = self.root
        return self.__entry__

    def init_anchor(
        self,
        anchor_id: str | None,
        default: NodeAnchor,
    ) -> NodeAnchor:
        """Load initial anchors."""
        if anchor_id:
            if isinstance(
                anchor := self.mem.find_by_id(UUID(anchor_id)), NodeAnchor
            ):
                return anchor
            raise ValueError(f"Invalid anchor id {anchor_id} !")
        return default if callable(default) elsedefault

    def validate_access(self) -> bool:
        """Validate access."""
        return self.root.has_read_access(self.entry)

    def close(self) -> None:
        """Close current ExecutionContext."""
        self.mem.close()
        EXECUTION_CONTEXT.set(None)

    @staticmethod
    def create(
        session: Optional[str] = None,
        root: Optional[str] = None,
        entry: Optional[str] = None,
        auto_close: bool = True,
    ) -> ExecutionContext:
        """Create ExecutionContext."""
        ctx = ExecutionContext()
        ctx.mem = ShelfStorage(session)
        ctx.reports = []

        if not isinstance(
            system_root := ctx.datasource.find_by_id(SUPER_ROOT_UUID), NodeAnchor
        ):
            system_root = Root().__jac__
            system_root.id = SUPER_ROOT_UUID
            ctx.datasource.set(system_root.id, system_root)

        ctx.system_root = system_root

        ctx.root = ctx.init_anchor(root, ctx.system_root)
        ctx.root.current_access_level = AccessLevel.WRITE

        ctx.__entry__ = entry

        if auto_close and (old_ctx := EXECUTION_CONTEXT.get(None)):
            old_ctx.close()

        EXECUTION_CONTEXT.set(ctx)

        return ctx

    @staticmethod
    def get() -> ExecutionContext:
        """Get current ExecutionContext."""
        if ctx := EXECUTION_CONTEXT.get(None):
            return ctx
        raise Exception("ExecutionContext is not yet available!")

    @staticmethod
    def get_root() -> Root:
        """Get current root."""
        if ctx := EXECUTION_CONTEXT.get(None):
            return cast(Root, ctx.root.architype)

        return SUPER_ROOT_ARCHITYPE


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
