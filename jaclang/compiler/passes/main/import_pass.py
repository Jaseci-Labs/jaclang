"""Static Import Pass.

This pass statically imports all modules used in import statements in the
current module. This pass is run before the def/decl pass to ensure that all
symbols are available for matching.
"""

import ast as py_ast
import importlib.util
import os
import subprocess
import sys
from typing import Optional


import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main import SubNodeTabPass
from jaclang.settings import settings
from jaclang.utils.helpers import import_target_to_relative_path, is_standard_lib_module


class JacImportPass(Pass):
    """Jac statically imports Jac modules."""

    def before_pass(self) -> None:
        """Run once before pass."""
        self.import_table: dict[str, ast.Module] = {}
        self.__py_imports: set[str] = set()
        self.py_resolve_list: set[str] = set()

    def enter_module(self, node: ast.Module) -> None:
        """Run Importer."""
        self.cur_node = node
        self.import_table[node.loc.mod_path] = node
        self.__py_imports.clear()
        self.__annex_impl(node)
        self.terminate()  # Turns off auto traversal for deliberate traversal
        self.run_again = True
        while self.run_again:
            self.run_again = False
            all_imports = self.get_all_sub_nodes(node, ast.ModulePath)
            for i in all_imports:
                self.process_import(node, i)
                self.enter_module_path(i)
            SubNodeTabPass(prior=self, input_ir=node)

        for i in self.get_all_sub_nodes(node, ast.AtomTrailer):
            self.enter_atom_trailer(i)

        node.mod_deps = self.import_table

    def process_import(self, node: ast.Module, i: ast.ModulePath) -> None:
        """Process an import."""
        lang = i.parent_of_type(ast.Import).hint.tag.value
        if lang == "jac" and not i.sub_module:
            self.import_jac_module(
                node=i,
                mod_path=node.loc.mod_path,
            )
        elif lang == "py":
            self.__py_imports.add(i.path_str.split(".")[0])
            self.py_resolve_list.add(i.path_str)

    def attach_mod_to_node(
        self, node: ast.ModulePath | ast.ModuleItem, mod: ast.Module | None
    ) -> None:
        """Attach a module to a node."""
        if mod:
            self.run_again = True
            node.sub_module = mod
            self.__annex_impl(mod)
            node.add_kids_right([mod], pos_update=False)

    def __annex_impl(self, node: ast.Module) -> None:
        """Annex impl and test modules."""
        if node.stub_only:
            return
        if not node.loc.mod_path:
            self.error("Module has no path")
        if not node.loc.mod_path.endswith(".jac"):
            return
        base_path = node.loc.mod_path[:-4]
        directory = os.path.dirname(node.loc.mod_path)
        if not directory:
            directory = os.getcwd()
            base_path = os.path.join(directory, base_path)
        impl_folder = base_path + ".impl"
        test_folder = base_path + ".test"
        search_files = [
            os.path.join(directory, impl_file) for impl_file in os.listdir(directory)
        ]
        if os.path.exists(impl_folder):
            search_files += [
                os.path.join(impl_folder, impl_file)
                for impl_file in os.listdir(impl_folder)
            ]
        if os.path.exists(test_folder):
            search_files += [
                os.path.join(test_folder, test_file)
                for test_file in os.listdir(test_folder)
            ]
        for cur_file in search_files:
            if node.loc.mod_path.endswith(cur_file):
                continue
            if (
                cur_file.startswith(f"{base_path}.")
                or impl_folder == os.path.dirname(cur_file)
            ) and cur_file.endswith(".impl.jac"):
                mod = self.import_jac_mod_from_file(cur_file)
                if mod:
                    node.impl_mod.append(mod)
                    node.add_kids_left([mod], pos_update=False)
                    mod.parent = node
            if (
                cur_file.startswith(f"{base_path}.")
                or test_folder == os.path.dirname(cur_file)
            ) and cur_file.endswith(".test.jac"):
                mod = self.import_jac_mod_from_file(cur_file)
                if mod:
                    node.test_mod.append(mod)
                    node.add_kids_right([mod], pos_update=False)
                    mod.parent = node

    def enter_module_path(self, node: ast.ModulePath) -> None:
        """Sub objects.

        path: Sequence[Token],
        alias: Optional[Name],
        sub_module: Optional[Module] = None,
        """
        if node.alias and node.sub_module:
            node.sub_module.name = node.alias.value
        # Items matched during def/decl pass

    def enter_atom_trailer(self, node: ast.AtomTrailer) -> None:
        """Iterate on AtomTrailer nodes to get python paths to resolve."""
        if node.as_attr_list[0].sym_name in self.__py_imports:
            self.py_resolve_list.add(".".join([i.sym_name for i in node.as_attr_list]))

    def import_jac_module(self, node: ast.ModulePath, mod_path: str) -> None:
        """Import a module."""
        self.cur_node = node  # impacts error reporting
        target = import_target_to_relative_path(
            level=node.level,
            target=node.path_str,
            base_path=os.path.dirname(node.loc.mod_path),
        )
        # If the module is a package (dir)
        if os.path.isdir(target):
            self.attach_mod_to_node(node, self.import_jac_mod_from_dir(target))
            import_node = node.parent_of_type(ast.Import)
            # And the import is a from import and I am the from module
            if node == import_node.from_loc:
                # Import all from items as modules or packages
                for i in import_node.items.items:
                    if isinstance(i, ast.ModuleItem):
                        from_mod_target = import_target_to_relative_path(
                            level=node.level,
                            target=node.path_str + "." + i.name.value,
                            base_path=os.path.dirname(node.loc.mod_path),
                        )
                        # If package
                        if os.path.isdir(from_mod_target):
                            self.attach_mod_to_node(
                                i, self.import_jac_mod_from_dir(from_mod_target)
                            )
                        # Else module
                        else:
                            self.attach_mod_to_node(
                                i, self.import_jac_mod_from_file(from_mod_target)
                            )
        else:
            self.attach_mod_to_node(node, self.import_jac_mod_from_file(target))

    def import_jac_mod_from_dir(self, target: str) -> ast.Module | None:
        """Import a module from a directory."""
        with_init = os.path.join(target, "__init__.jac")
        if os.path.exists(with_init):
            return self.import_jac_mod_from_file(with_init)
        else:
            return ast.Module(
                name=target.split(os.path.sep)[-1],
                source=ast.JacSource("", mod_path=target),
                doc=None,
                body=[],
                is_imported=False,
                stub_only=True,
                kid=[ast.EmptyToken()],
            )

    def import_jac_mod_from_file(self, target: str) -> ast.Module | None:
        """Import a module from a file."""
        from jaclang.compiler.compile import jac_file_to_pass
        from jaclang.compiler.passes.main import SubNodeTabPass

        if not os.path.exists(target):
            self.error(f"Could not find module {target}")
            return None
        if target in self.import_table:
            return self.import_table[target]
        try:
            mod_pass = jac_file_to_pass(file_path=target, target=SubNodeTabPass)
            self.errors_had += mod_pass.errors_had
            self.warnings_had += mod_pass.warnings_had
            mod = mod_pass.ir
        except Exception as e:
            print(e)
            mod = None
        if isinstance(mod, ast.Module):
            self.import_table[target] = mod
            mod.is_imported = True
            mod.body = [x for x in mod.body if not isinstance(x, ast.AstImplOnlyNode)]
            return mod
        else:
            self.error(f"Module {target} is not a valid Jac module.")
            return None

    def get_py_lib_path(self, import_path: str) -> Optional[str]:
        """Try to get the stub path of a python module."""
        base_library = import_path.split(".")[0]

        try:
            spec = importlib.util.find_spec(base_library)
            lib_path = spec.origin if spec else None
        except ModuleNotFoundError:
            lib_path = None

        if lib_path is None:
            return None
        if os.path.sep not in lib_path:
            return None

        if lib_path.endswith("py") and os.path.isfile(lib_path.replace(".py", ".pyi")):
            lib_path = lib_path.replace(".py", ".pyi")

        base_path = lib_path[: lib_path.rindex("/")]

        for i in import_path.split(".")[1:]:

            # TODO: Check this branch
            if os.path.isdir(os.path.join(base_path, i)):
                lib_path = os.path.join(base_path, i)

            elif os.path.isfile(os.path.join(base_path, i + ".pyi")):
                return os.path.join(base_path, i + ".pyi")

            elif os.path.isfile(os.path.join(base_path, i + ".py")):
                return os.path.join(base_path, i + ".py")

        return lib_path

    def grep(self, file_path: str, regex: str) -> list[str]:
        """Search for a word inside a directory."""
        command = ["grep", regex, file_path]
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.split("\n")

    def after_pass(self) -> None:
        """Call pass after_pass."""
        from jaclang.compiler.passes.main import PyastBuildPass

        # This part to handle importing/creating parent modules in case of doing
        # import a.b.c
        # without it code will crash as it will create a.b.c as a module and at linking
        # it will try to link each a, b and c as separate modules which will crash
        more_modules_to_import = []
        for i in self.py_resolve_list:
            if "." in i:
                name_list = i.split(".")
                for index in range(len(name_list)):
                    more_modules_to_import.append(".".join(name_list[:index]))

        for i in more_modules_to_import:
            self.py_resolve_list.add(i)

        sorted_resolve_list = list(self.py_resolve_list)
        sorted_resolve_list.sort()

        py_mod_map: dict[str, tuple[ast.Module, list[str]]] = {}

        for i in sorted_resolve_list:

            expected_file = self.get_py_lib_path(i)

            if expected_file is None:
                continue

            if not os.path.isfile(expected_file):
                continue

            # final_target = i.split(".")[-1]
            # base_file = i.split(".")[0]

            # if "." in i:
            #     print(self.grep(file_path=expected_file, regex=fr"\s*{final_target}\s*="))

            if expected_file not in py_mod_map:
                with open(expected_file, "r", encoding="utf-8") as f:
                    py_mod_map[expected_file] = (
                        PyastBuildPass(
                            input_ir=ast.PythonModuleAst(
                                py_ast.parse(f.read()), mod_path=expected_file
                            ),
                        ).ir,
                        [i],
                    )
                    SubNodeTabPass(prior=self, input_ir=py_mod_map[expected_file][0])
                    py_mod_map[expected_file][0].py_lib = True
            else:
                py_mod_map[expected_file][1].append(i)

        attached_modules: dict[str, ast.Module] = {}
        for i in py_mod_map:
            mode = py_mod_map[i][0]
            name_list = py_mod_map[i][1]  # List of names that uses the modules
            name_list.sort()
            mode_name = name_list[0].split(".")[
                -1
            ]  # Less name in length will be the module name itself
            mode.name = mode_name

            assert isinstance(self.ir, ast.Module)
            if mode_name == name_list[0]:
                self.attach_mod_to_node(self.ir, mode)
                attached_modules[mode.name] = mode
                mode.parent = self.ir
            else:
                # TODO: Fix me when an issue happens
                parent_mode = attached_modules[name_list[0].split(".")[-2]]
                self.attach_mod_to_node(parent_mode, mode)
                # attached_modules[mode] = mode
                mode.parent = parent_mode


class PyImportPass(JacImportPass):
    """Jac statically imports Python modules."""

    def before_pass(self) -> None:
        """Only run pass if settings are set to raise python."""
        super().before_pass()
        if not settings.py_raise:
            self.terminate()

    def process_import(self, node: ast.Module, i: ast.ModulePath) -> None:
        """Process an import."""
        lang = i.parent_of_type(ast.Import).hint.tag.value
        if lang == "py" and not i.sub_module and not is_standard_lib_module(i.path_str):
            mod = self.import_py_module(node=i, mod_path=node.loc.mod_path)
            if mod:
                i.sub_module = mod
                i.add_kids_right([mod], pos_update=False)
                if settings.py_raise_deep:
                    self.run_again = True

    def import_py_module(
        self, node: ast.ModulePath, mod_path: str
    ) -> Optional[ast.Module]:
        """Import a module."""
        from jaclang.compiler.passes.main import PyastBuildPass

        base_dir = os.path.dirname(mod_path)
        sys.path.append(base_dir)
        try:
            # Dynamically import the module
            spec = importlib.util.find_spec(node.path_str)
            sys.path.remove(base_dir)
            if spec and spec.origin and spec.origin not in {None, "built-in", "frozen"}:
                if spec.origin in self.import_table:
                    return self.import_table[spec.origin]
                with open(spec.origin, "r", encoding="utf-8") as f:
                    # print(f"\nImporting python module {node.path_str}")
                    mod = PyastBuildPass(
                        input_ir=ast.PythonModuleAst(
                            py_ast.parse(f.read()), mod_path=spec.origin
                        ),
                    ).ir
                if mod:
                    self.import_table[spec.origin] = mod
                    return mod
                else:
                    raise self.ice(
                        f"Failed to import python module {node.path_str}: {spec.origin}"
                    )
        except Exception as e:
            if "Empty kid for Token ModulePath" in str(e) or "utf-8" in str(e):  # FIXME
                return None
            self.error(
                f"Failed to import python module {node.path_str}: {e}",
                node_override=node,
            )
            raise e
        return None
