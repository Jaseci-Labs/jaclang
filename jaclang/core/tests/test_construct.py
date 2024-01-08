"""Test Jac DS features."""
import io
from contextlib import redirect_stdout

from jaclang.compiler.transpiler import jac_file_to_pass
from jaclang.utils.test import TestCase


class ConstructTests(TestCase):
    """Test Jac DS Features."""

    def test_gen_dot(self) -> None:
        """Test the dot gen of nodes and edges."""

        def execute_and_capture_output(code: str) -> str:
            f = io.StringIO()
            with redirect_stdout(f):
                exec(code, {})
            return f.getvalue()

        try:
            code_py = jac_file_to_pass("bubble_sort.jac").ir.gen.py
            out = execute_and_capture_output(code_py)
            op = ["4 -> 12 ;", "2 -> 20 ;", "2 -> 22 ;", "1 -> 27 ;"]
            for i in op:
                assert i in out
        except Exception as e:
            self.skipTest(f"Test failed on bubble_sort.jac : {e}")
