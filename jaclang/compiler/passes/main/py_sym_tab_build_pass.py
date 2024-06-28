"""Symbol table tree build pass for Jaseci Ast.

This pass builds the symbol table tree for the Jaseci Ast. It also adds symbols
for globals, imports, architypes, and abilities declarations and definitions.
"""

import importlib
import inspect

import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main import JacImportPass
from jaclang.compiler.symtable import PySymbolTable, SymbolTable


class PySymTabBuildPass(Pass):
    """Jac Symbol table build pass for python imports and types."""

    def push_scope(self, name: str, key_node: ast.AstNode) -> None:
        """Push scope."""
        self.cur_sym_tab.append(self.cur_scope.push_py_scope(name, key_node))

    def pop_scope(self) -> SymbolTable:
        """Pop scope."""
        return self.cur_sym_tab.pop()

    def to_scope(self, scope_name: str) -> SymbolTable:
        """Go to another scope."""
        scope = self.cur_scope.find_scope(scope_name)
        if scope:
            self.cur_sym_tab.append(scope)
        return scope

    @property
    def cur_py_scope(self) -> PySymbolTable:
        """Return current python scope."""
        assert isinstance(self.cur_sym_tab[-1], PySymbolTable)
        return self.cur_sym_tab[-1]

    @property
    def cur_scope(self) -> SymbolTable:
        """Return current python scope."""
        return self.cur_sym_tab[-1]

    def before_pass(self) -> None:
        """Before pass."""
        self.cur_sym_tab: list[SymbolTable] = [self.ir.sym_tab]
        py_mods = list(JacImportPass.python_modules_to_import)
        py_mods.sort()

        while len(py_mods):
            imported_mods = []
            for py_import in py_mods:
                self.__create_py_mod_symbols(py_import)
                imported_mods.append(py_import)
            for i in imported_mods:
                py_mods.remove(i)

        self.cur_sym_tab: list[SymbolTable] = [self.ir.sym_tab]

    def enter_atom_trailer(self, node: ast.AtomTrailer) -> None:
        """For each atom trailer check if the nodes are related to python modules."""
        self.prune()
        attr_list = node.as_attr_list
        if attr_list[0].sym_name not in JacImportPass.python_modules_to_import:
            return
        import_href = []
        for i in attr_list:
            if self.cur_scope.find_scope(i.sym_name) is None:
                self.__create_py_mod_symbols(".".join(import_href + [i.sym_name]))

            import_href.append(i.sym_name)
            self.to_scope(i.sym_name)
            i.type_sym_tab = self.cur_py_scope

    def __create_py_mod_symbols(self, py_mod_name: str) -> None:
        while (
            self.cur_scope.name != self.ir.sym_tab.name
            and self.cur_scope.name not in py_mod_name
        ):
            self.pop_scope()

        self.push_scope(py_mod_name.split(".")[-1], self.ir)
        for i in self.__get_all_symbols(py_mod_name):
            self.cur_py_scope.insert(
                ast.Name(
                    i["file"],
                    i["name"],
                    i["name"],
                    i["start_line"],
                    i["end_line"],
                    0,
                    0,
                    0,
                    0,
                )
            )

    def __get_all_symbols(self, py_name: str) -> list[str]:
        out = []
        py_name = py_name.split(".")
        obj = importlib.import_module(py_name[0])
        for i in py_name[1:]:
            if not hasattr(obj, i):
                return []
            obj = getattr(obj, i)
            if inspect.ismodule(obj):
                obj = importlib.import_module(".".join(py_name[: py_name.index(i)]))

        for name, member in inspect.getmembers(obj):
            member_info = {
                "name": name,
                "type": (
                    "module"
                    if inspect.ismodule(member)
                    else (
                        "class"
                        if inspect.isclass(member)
                        else (
                            "function"
                            if inspect.isfunction(member)
                            else (
                                "builtin function"
                                if inspect.isbuiltin(member)
                                else "other"
                            )
                        )
                    )
                ),
                "file": "",
                "start_line": 0,
                "end_line": 0,
            }

            try:
                member_info["file"] = inspect.getfile(member)
                lines = inspect.getsourcelines(member)
                member_info["start_line"] = lines[1]
                member_info["end_line"] = lines[1] + 1
            except TypeError:
                pass
            except OSError:
                pass

            out.append(member_info)
        return out
