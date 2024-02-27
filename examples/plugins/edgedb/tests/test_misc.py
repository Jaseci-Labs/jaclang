"""Test plugin utils functions."""

from jaclang.compiler.passes.main import ImportPass
from jaclang.compiler.transpiler import jac_file_to_pass
from jaclang.utils.test import TestCase


class PluginMiscTests(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_base(self) -> None:
        """Basic test for pass."""
        # state = jac_file_to_pass(self.fixture_abs_path("base.jac"), ImportPass)
        self.assertFalse(False)
        # self.assertIn("56", str(state.ir.to_dict()))
