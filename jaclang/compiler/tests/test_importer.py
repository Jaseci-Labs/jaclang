"""Tests for Jac Loader."""

import io
import sys

from jaclang import jac_import
from jaclang.cli import cli
from jaclang.plugin.feature import JacFeature as Jac
from jaclang.utils.test import TestCase


class TestLoader(TestCase):
    """Test Jac self.prse."""

    def setUp(self) -> None:
        """Set up test."""
        Jac.new_context()
        return super().setUp()

    def test_import_basic_python(self) -> None:
        """Test basic self loading."""
        Jac.new_context(base_path=self.fixture_abs_path(__file__))
        (h,) = jac_import("fixtures.hello_world", base_path=__file__)
        self.assertEqual(h.hello(), "Hello World!")  # type: ignore

    def test_modules_correct(self) -> None:
        """Test basic self loading."""
        Jac.new_context(base_path=self.fixture_abs_path(__file__))
        jac_import("fixtures.hello_world", base_path=__file__)
        self.assertIn("module 'fixtures.hello_world'", str(sys.modules))
        self.assertIn("/tests/fixtures/hello_world.jac", str(sys.modules))

    def test_jac_py_import(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.run(self.fixture_abs_path("../../../tests/fixtures/jp_importer.jac"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("Hello World!", stdout_value)
        self.assertIn(
            "{SomeObj(a=10): 'check'} [MyObj(apple=5, banana=7), MyObj(apple=5, banana=7)]",
            stdout_value,
        )

    def test_jac_py_import_auto(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        cli.run(self.fixture_abs_path("../../../tests/fixtures/jp_importer_auto.jac"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("Hello World!", stdout_value)
        self.assertIn(
            "{SomeObj(a=10): 'check'} [MyObj(apple=5, banana=7), MyObj(apple=5, banana=7)]",
            stdout_value,
        )
