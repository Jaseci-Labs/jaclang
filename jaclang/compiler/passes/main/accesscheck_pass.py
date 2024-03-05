"""Access check pass for the Jac compiler.

This pass checks for access to variables and functions in the Jac language.

"""

import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes.main.sym_tab_build_pass import SymTabPass
from jaclang.compiler.symtable import SymbolAccess


class AccessCheckPass(SymTabPass):
    """Jac Ast Access Check pass."""

    def after_pass(self) -> None:
        """After pass."""
        pass

    def enter_global_vars(self, node: ast.GlobalVars) -> None:
        """Sub objects.

        access: Optional[SubTag[Token]],
        assignments: SubNodeList[Assignment],
        is_frozen: bool,
        """
        pass

    def enter_module(self, node: ast.Module) -> None:
        """Sub objects.

        name: str,
        doc: Token,
        body: Optional['Elements'],
        mod_path: str,
        is_imported: bool,
        """

    def enter_architype(self, node: ast.Architype) -> None:
        """Sub objects.

        name: Name,
        arch_type: Token,
        access: Optional[SubTag[Token]],
        base_classes: Optional[SubNodeList[Expr]],
        body: Optional[SubNodeList[ArchBlockStmt] | ArchDef],
        decorators: Optional[SubNodeList[Expr]] = None,
        """
        pass

    def enter_enum(self, node: ast.Enum) -> None:
        """Sub objects.

        name: Name,
        access: Optional[SubTag[Token]],
        base_classes: Optional[SubNodeList[Expr]],
        body: Optional[SubNodeList[EnumBlockStmt] | EnumDef],
        decorators: Optional[SubNodeList[Expr]] = None,
        """
        pass

    def enter_ability(self, node: ast.Ability) -> None:
        """Sub objects.

        name_ref: NameSpec,
        is_func: bool,
        is_async: bool,
        is_override: bool,
        is_static: bool,
        is_abstract: bool,
        access: Optional[SubTag[Token]],
        signature: Optional[FuncSignature | EventSignature],
        body: Optional[SubNodeList[CodeBlockStmt] | AbilityDef],
        decorators: Optional[SubNodeList[Expr]] = None,
        """
        pass

    def enter_sub_node_list(self, node: ast.SubNodeList) -> None:
        """Sub objects.

        items: list[T]
        """

    def enter_arch_has(self, node: ast.ArchHas) -> None:
        """Sub objects.

        is_static: bool,
        access: Optional[SubTag[Token]],
        vars: SubNodeList[HasVar],
        is_frozen: bool,
        """
        pass

    def enter_atom_trailer(self, node: ast.AtomTrailer) -> None:
        """Sub objects.

        access: Optional[SubTag[Token]],
        """
        pass

    def enter_func_call(self, node: ast.FuncCall) -> None:
        """Sub objects.

        target: AtomType,
        params: Optional[SubNodeList[ExprType | Assignment]],
        """

    def enter_name(self, node: ast.Name) -> None:
        """Sub objects.

        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """

        def are_files_same(file_path1: str, file_path2: str) -> bool:
            lines1 = [
                line.strip() for line in file_path1 if not line.strip().startswith("/")
            ]
            lines2 = [
                line.strip() for line in file_path2 if not line.strip().startswith("//")
            ]
            return lines1 == lines2

        # print(
        #     (node.sym_link.decl.loc.mod_path) if node.sym_link else None,
        #     ("mod-> ", node.loc.mod_path),
        # )
        if isinstance(node.sym_tab, ast.SymbolTable):
            x = node.sym_tab.lookup(node.sym_name)
        # if node.sym_link and node.sym_link.decl.sym_tab.name==node.sym_tab.name and x.access==SymbolAccess.PRIVATE:
        #     print('errorrr ...!!!! ')
        if (
            x
            and node.sym_link
            and x.access == SymbolAccess.PRIVATE
            and not (are_files_same(node.sym_link.decl.loc.mod_path, node.loc.mod_path))
        ):
            # raise self.error(
            #     f'Access to private variable "{node.sym_name}" from {node.loc.mod_path}'
            #     f" to {node.sym_link.decl.loc.mod_path}"
            # )
            return self.error(
                f'Access to private variable "{node.sym_name}" from {node.loc.mod_path}'
                f" to {node.sym_link.decl.loc.mod_path}"
            )
