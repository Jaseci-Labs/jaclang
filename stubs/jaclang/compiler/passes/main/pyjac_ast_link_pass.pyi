import ast as ast3
import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes import Pass as Pass

class PyJacAstLinkPass(Pass):
    def link_jac_py_nodes(
        self, jac_node: ast.AstNode, py_nodes: list[ast3.AST]
    ) -> None: ...
    def exit_module_path(self, node: ast.ModulePath) -> None: ...
    def exit_architype(self, node: ast.Architype) -> None: ...
    def exit_arch_def(self, node: ast.ArchDef) -> None: ...
    def exit_enum(self, node: ast.Enum) -> None: ...
    def exit_enum_def(self, node: ast.EnumDef) -> None: ...
    def exit_ability(self, node: ast.Ability) -> None: ...
    def exit_ability_def(self, node: ast.AbilityDef) -> None: ...
    def exit_param_var(self, node: ast.ParamVar) -> None: ...
    def exit_except(self, node: ast.Except) -> None: ...
    def exit_expr_as_item(self, node: ast.ExprAsItem) -> None: ...
    def exit_global_stmt(self, node: ast.GlobalStmt) -> None: ...
    def exit_non_local_stmt(self, node: ast.NonLocalStmt) -> None: ...
    def exit_k_w_pair(self, node: ast.KWPair) -> None: ...
    def exit_atom_trailer(self, node: ast.AtomTrailer) -> None: ...
