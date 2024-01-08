"""Test Jac DS features."""
import io
from contextlib import redirect_stdout

from jaclang.compiler.transpiler import jac_file_to_pass


def test_dot_gen() -> None:
    """Test the dot gen of nodes and edges."""

    def execute_and_capture_output(code: str) -> str:
        f = io.StringIO()
        with redirect_stdout(f):
            exec(code, {})
        return f.getvalue()

    code_py = jac_file_to_pass("bubble_sort.jac").ir.gen.py
    out = execute_and_capture_output(code_py)
    op = [
        "4 -> 12 ;",
        "2 -> 20 ;",
        "2 -> 22 ;",
        "1 -> 27 ;",
        "0 -> 1 ;",
        "6 -> 7 ;",
        "0 -> 31 ;",
    ]
    for i in op:
        assert i in out
