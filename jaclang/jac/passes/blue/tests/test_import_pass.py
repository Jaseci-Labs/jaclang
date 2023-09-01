"""Test pass module."""
from jaclang.jac.passes.blue import ImportPass
from jaclang.jac.transpiler import Transpiler
from jaclang.utils.test import TestCase


class ImportPassPassTests(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_pygen_jac_cli(self) -> None:
        """Basic test for pass."""
        state = Transpiler.to_pass(self.fixture_abs_path("base.jac"), "", ImportPass)
        self.assertFalse(state.errors_had)
        self.assertIn("56", str(state.ir.to_dict()))
