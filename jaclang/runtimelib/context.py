"""Core constructs for Jac Language."""

from __future__ import annotations

import unittest
from contextvars import ContextVar
from typing import Any, Callable, Optional
from uuid import UUID

from .architype import NodeAnchor, Root
from .machine import JacMachine, JacProgram
from .memory import ShelfStorage


EXECUTION_CONTEXT = ContextVar[Optional["ExecutionContext"]]("ExecutionContext")
SUPER_ROOT_UUID = "00000000-0000-0000-0000-000000000000"


class ExecutionContext:
    """Execution Context."""

    jac_machine: JacMachine
    datasource: ShelfStorage
    reports: list[Any]
    system_root: NodeAnchor
    root: NodeAnchor
    entry: NodeAnchor

    def generate_system_root(self) -> NodeAnchor:
        """Generate default system root."""
        architype = object.__new__(Root)
        system_root = architype.__jac__ = NodeAnchor(
            architype, id=UUID(SUPER_ROOT_UUID), persistent=True
        )
        self.datasource.set(system_root.id, system_root)
        return system_root

    def load(
        self,
        anchor_id: str | None,
        default: NodeAnchor | Callable[[], NodeAnchor],
    ) -> NodeAnchor:
        """Load initial anchors."""
        if anchor_id and isinstance(
            anchor := self.datasource.find_by_id(UUID(anchor_id)), NodeAnchor
        ):
            return anchor
        return default() if callable(default) else default

    def close(self) -> None:
        """Clean up context."""
        self.datasource.close()

    @staticmethod
    def create(
        base_path: str = "",
        session: Optional[str] = None,
        root: Optional[str] = None,
        entry: Optional[str] = None,
    ) -> ExecutionContext:
        """Create JacContext."""
        ctx = ExecutionContext()
        ctx.jac_machine = JacMachine(base_path)
        ctx.jac_machine.attach_program(JacProgram(mod_bundle=None, bytecode=None))
        ctx.datasource = ShelfStorage(session)
        ctx.reports = []
        ctx.system_root = ctx.load(SUPER_ROOT_UUID, ctx.generate_system_root)
        ctx.root = ctx.load(root, ctx.system_root)
        ctx.entry = ctx.load(entry, ctx.root)

        if _ctx := EXECUTION_CONTEXT.get(None):
            _ctx.close()
        EXECUTION_CONTEXT.set(ctx)

        return ctx

    @staticmethod
    def get() -> ExecutionContext:
        """Get current ExecutionContext."""
        if not isinstance(ctx := EXECUTION_CONTEXT.get(None), ExecutionContext):
            raise Exception("ExecutionContext is not yet available!")
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
