import jaclang.compiler.absyntree as ast
from jaclang.compiler.constant import SymbolAccess as SymbolAccess
from jaclang.compiler.passes import Pass as Pass
from jaclang.compiler.symtable import SymbolTable as SymbolTable
from jaclang.settings import settings as settings

class AccessCheckPass(Pass):
    def after_pass(self) -> None: ...
    def exit_node(self, node: ast.AstNode) -> None: ...
    def access_check(self, node: ast.Name) -> None: ...
    def access_register(
        self, node: ast.AstSymbolNode, acc_tag: SymbolAccess | None = None
    ) -> None: ...
    def enter_global_vars(self, node: ast.GlobalVars) -> None: ...
    def enter_module(self, node: ast.Module) -> None: ...
    def enter_architype(self, node: ast.Architype) -> None: ...
    def enter_enum(self, node: ast.Enum) -> None: ...
    def enter_ability(self, node: ast.Ability) -> None: ...
    def enter_sub_node_list(self, node: ast.SubNodeList) -> None: ...
    def enter_arch_has(self, node: ast.ArchHas) -> None: ...
    def enter_atom_trailer(self, node: ast.AtomTrailer) -> None: ...
    def enter_func_call(self, node: ast.FuncCall) -> None: ...
    def enter_name(self, node: ast.Name) -> None: ...
