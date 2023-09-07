"""Analyze Pass."""
from typing import Any

import jaclang.jac.absyntree as ast
from jaclang.jac.constant import Tokens as Tok
from jaclang.jac.passes import Pass
from jaclang.jac.sym_table import SymbolTable


class AnalyzePass(Pass, SymbolTable):
    """Analyze archtype pass."""

    def exit_arch_block(self, node: ast.ArchBlock) -> None:
        """Sub objects.

        members: list['ArchHas | Ability'],
        """
        # Tags all function signatures whether method style or event style
        if (
            isinstance(node.parent, ast.Architype)
            and node.parent.arch_type.name == Tok.KW_WALKER
        ):
            for i in self.get_all_sub_nodes(
                node, ast.VisitStmt, brute_force=True
            ):  # TODO: Remove brute
                i.from_walker = True
            for i in self.get_all_sub_nodes(
                node, ast.DisengageStmt, brute_force=True
            ):  # TODO: Remove brute
                i.from_walker = True
            for i in self.get_all_sub_nodes(
                node, ast.EdgeOpRef, brute_force=True
            ):  # TODO: Remove brute
                i.from_walker = True
