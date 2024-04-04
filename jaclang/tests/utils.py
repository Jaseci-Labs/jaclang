"""Helper functions for tests."""

from __future__ import annotations

import jaclang.compiler.absyntree as ast
from jaclang.compiler.compile import jac_file_to_pass
from jaclang.compiler.passes.main.import_pass import ImportPass  # noqa: I100


def get_child_import_module(mod_path: str) -> str:
    """Get child module node from main root module node."""
    for i in jac_file_to_pass(mod_path, target=ImportPass).ir.kid:
        if isinstance(i, ast.Import) and i.kid:
            for j in i.kid:
                if isinstance(j, ast.ModulePath) and j.kid:
                    for k in j.kid:
                        if isinstance(k, ast.Module):
                            break
                    break
    return k.__class__.__bases__[0].unparse(k)
