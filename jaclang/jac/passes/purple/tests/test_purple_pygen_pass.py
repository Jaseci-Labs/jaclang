"""Tests for the PurplePygenPass."""
import io
import sys

from jaclang.jac.transpiler import Transpiler
from jaclang.jac.passes.purple import PurplePygenPass, pass_schedule as purple_pass_schedule
from jaclang.utils.test import TestCaseMicroSuite


class PurplePygenPassTests(TestCaseMicroSuite):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_simple_jac_red(self) -> None:
        """Parse micro jac file."""
        from jaclang import jac_purple_import

        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_purple_import("micro.simple_walk", self.fixture_abs_path("../../../../../../examples/"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            stdout_value,
            "Value: -1\nValue: 0\nValue: 1\nValue: 2\nValue: 3\nValue: 4"
            "\nValue: 5\nValue: 6\nValue: 7\nFinal Value: 8\nDone walking.\n",
        )

    def micro_suite_test(self, filename: str) -> None:
        """Parse micro jac file."""
        code_gen = Transpiler.transpile(self.fixture_abs_path(filename), target=PurplePygenPass, pass_schedule=purple_pass_schedule)
        self.assertGreater(len(code_gen), 10)


PurplePygenPassTests.self_attach_micro_tests()
