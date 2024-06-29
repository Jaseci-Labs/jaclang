"""Symbol table tree build pass for Jaseci Ast.

This pass builds the symbol table tree for the Jaseci Ast. It also adds symbols
for globals, imports, architypes, and abilities declarations and definitions.
"""

import importlib
import inspect
import os

import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main import JacImportPass
from jaclang.compiler.symtable import PySymbolTable, SymbolTable
from jaclang.settings import settings


class PySymTabBuildPass(Pass):
    """Jac Symbol table build pass for python imports and types."""

    def __debug_print(self, *args) -> None:
        if settings.py_symtab_debug:
            print("PySymTabBuildPass:", *args)

    def push_scope(self, name: str, key_node: ast.AstNode) -> None:
        """Push scope."""
        self.__debug_print(
            f'Adding new scope "{name}", in side the current scope "{self.cur_scope.sym_dotted_name}"'
        )
        self.cur_sym_tab.append(self.cur_scope.push_py_scope(name, key_node))
        self.__debug_print(
            f"Moving current scope to be {self.cur_scope.sym_dotted_name}"
        )

    def pop_scope(self) -> SymbolTable:
        """Pop scope."""
        out = self.cur_sym_tab.pop()
        self.__debug_print(
            f"Moving current scope to be {self.cur_scope.sym_dotted_name}"
        )
        return out

    def to_scope(self, scope_name: str) -> SymbolTable | None:
        """Go to another scope."""
        scope = self.cur_scope.find_scope(scope_name)
        if scope:
            self.cur_sym_tab.append(scope)
            self.__debug_print(
                f"Moving current scope to be {self.cur_scope.sym_dotted_name}"
            )
        return scope

    def to_main_scope(self) -> None:
        """Go to the main scope (jac main scope)."""
        while len(self.cur_sym_tab) > 1:
            self.pop_scope()

    @property
    def cur_py_scope(self) -> PySymbolTable:
        """Return current python scope."""
        assert isinstance(self.cur_sym_tab[-1], PySymbolTable)
        return self.cur_sym_tab[-1]

    @property
    def cur_scope(self) -> SymbolTable:
        """Return current scope."""
        return self.cur_sym_tab[-1]

    def before_pass(self) -> None:
        """Before pass."""
        super().before_pass()
        self.cur_sym_tab: list[SymbolTable] = [self.ir.sym_tab]
        py_mods = list(JacImportPass.python_modules_to_import)
        py_mods.sort()

        while len(py_mods):
            imported_mods = []
            for py_import in py_mods:
                self.create_py_mod_symbols(py_import)
                imported_mods.append(py_import)
            for i in imported_mods:
                py_mods.remove(i)

        self.cur_sym_tab = [self.ir.sym_tab]

    def enter_atom_trailer(self, node: ast.AtomTrailer) -> None:
        """For each atom trailer check if the nodes are related to python modules."""
        # prune the traversing as I am only interested in the upper atom trailer node
        # this will be either a type annotation or it will be calling a function
        # directly from a python module
        self.prune()
        attr_list = node.as_attr_list

        # Make sure that the first item in the attr list is indeed an imported py module
        if attr_list[0].sym_name not in JacImportPass.python_modules_to_import:
            return

        import_href: list[str] = []
        for i in attr_list:

            # Check the module is already imported or not
            if self.cur_scope.find_scope(i.sym_name) is None:
                self.create_py_mod_symbols(".".join(import_href + [i.sym_name]))

            import_href.append(i.sym_name)
            self.to_scope(i.sym_name)
            # updating the node to point to the newly created sym table
            i.type_sym_tab = self.cur_py_scope

        # Go back to the main scope
        self.to_main_scope()

    def create_py_mod_symbols(self, py_mod_name: str) -> None:
        """Add symbols related to a python object in the symbol table."""
        # Check which scope we are in and if we need to pop the current scope
        # The top scope should be jac file name and for each module we import
        # symbols from, make sure to have the correct scope

        # Ignoring typing module save us 80% of time
        if py_mod_name.startswith("typing"):
            return

        while (
            self.cur_scope.name != self.ir.sym_tab.name
            and self.cur_scope.name not in py_mod_name
        ):
            self.pop_scope()

        self.__debug_print("**** Importing data to that scope ****")
        symbol_list = self.get_all_symbols(py_mod_name)

        if len(symbol_list) > 0:
            self.push_scope(py_mod_name.split(".")[-1], self.ir)

        for i in symbol_list:
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
        self.__debug_print("**************************************")

    def get_all_symbols(self, py_name: str) -> list[dict]:
        """Get all the symbols from a python module.

        Retrieves all symbols (e.g., functions, classes) within the specified Python module.

        Args:
            py_name (str): The name of the Python module to inspect. Can be a hierarchical name
                        separated by dots (e.g., 'module.submodule.subsubmodule').

        Returns:
            list[dict]: A list of dictionaries, each containing information about a symbol:
                        {
                            "name": str,       # Name of the symbol
                            "file": str,       # File where the symbol is defined
                            "start_line": int, # Starting line number in the file
                            "end_line": int    # Ending line number in the file
                        }

        Notes:
            - This method dynamically imports the specified Python module and its submodules.
            - It uses introspection (`inspect` module) to gather information about each symbol.
            - If a submodule or symbol cannot be found, or if introspection fails, empty lists
            or default values are returned for affected symbols.
        """
        self.__debug_print(f"Trying to import {py_name}")
        out = []
        py_name_lists = py_name.split(".")
        obj = importlib.import_module(py_name_lists[0])
        stop_importing = False

        for i in py_name_lists[1:]:
            if stop_importing:
                self.__debug_print(
                    f"Cannot resolve the name {py_name_lists}, check this!!!"
                )
                return []

            next_obj_fname = ".".join(py_name_lists[: py_name_lists.index(i) + 1])
            parent_obj_fname = ".".join(py_name_lists[: py_name_lists.index(i)])

            if not hasattr(obj, i):
                self.__debug_print(f"Cannot find {i} inside {parent_obj_fname}")
                return []
            obj = getattr(obj, i)

            if inspect.ismodule(obj):
                self.__debug_print(f"Found module {i}, importing {next_obj_fname}")
                obj = importlib.import_module(next_obj_fname)
            else:
                stop_importing = True

        self.__debug_print(f"Getting Symbols from {py_name}, type={type(obj)}")

        if isinstance(obj, (int, float, bool)):
            self.__debug_print("No need to get symbols from that object")
            return []

        for name, member in inspect.getmembers(obj):
            member_info = {
                "name": name,
                "file": "",
                "start_line": 0,
                "end_line": 0,
            }

            try:

                # Extracting python file, stub module if it's a .so file
                orig_file = inspect.getfile(member)
                if orig_file.endswith(".so"):
                    dir_path = orig_file[: orig_file.rindex("/")]
                    f = orig_file.replace(dir_path, "")
                    f = f[: f.index(".")]
                    if os.path.isfile(dir_path + f + ".pyi"):
                        orig_file = dir_path + f + ".pyi"
                    elif os.path.isfile(dir_path + f + ".py"):
                        orig_file = dir_path + f + ".py"

                member_info["file"] = orig_file
                lines = inspect.getsourcelines(member)
                member_info["start_line"] = lines[1]
                member_info["end_line"] = lines[1] + 1
            except TypeError:
                pass
            except OSError:
                pass

            out.append(member_info)
        return out
