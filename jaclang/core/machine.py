"""Jac Machine Module."""

import importlib
import marshal
import types
from os import getcwd, path
from typing import Dict, Optional, Union

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging


class JacProgram:
    """Represents a Jac program containing bytecode and its associated module."""

    def __init__(
        self,
        filename: str,
        base_path: str,
        cachable: bool = True,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = "jac",
        items: Optional[dict[str, Union[str, bool]]] = None,
        absorb: bool = False,
        mdl_alias: Optional[str] = None,
    ) -> None:
        """Initialize a JacProgram instance.

        Args:
            filename (str): The filename of the Jac program.
            base_path (str): The base path to use.
            cachable (bool): Whether the program is cachable. Defaults to True.
            override_name (Optional[str]): An optional name override for the module. Defaults to None.
            mod_bundle (Optional[Module]): An optional module bundle. Defaults to None.
            lng (Optional[str]): The language of the module. Defaults to "jac".
            items (Optional[dict[str, Union[str, bool]]]): Optional items to import.
            absorb (bool): Whether to absorb the imported module into the main module.
            mdl_alias (Optional[str]): Optional alias for the module.
        """
        self.bytecode: Optional[bytes] = None
        self.module: Optional[types.ModuleType] = None
        self.load_program(
            filename,
            base_path,
            cachable,
            override_name,
            mod_bundle,
            lng,
            items,
            absorb,
            mdl_alias,
        )

    def load_program(
        self,
        filename: str,
        base_path: str,
        cachable: bool,
        override_name: Optional[str],
        mod_bundle: Optional[Module],
        lng: Optional[str],
        items: Optional[dict[str, Union[str, bool]]],
        absorb: bool,
        mdl_alias: Optional[str],
    ) -> None:
        """Load the Jac program from a file."""
        try:
            module_name = path.splitext(path.basename(filename))[0]
            # print(f"Filename: {filename}")

            # Handle both absolute and relative paths correctly
            if path.isabs(filename):
                full_target = path.normpath(filename)
            else:
                caller_dir = get_caller_dir(base_path)
                full_target = path.normpath(path.join(caller_dir, filename))

            # print(f"Full target: {full_target}")

            if lng == "py":
                # Handle Python module import
                module = py_import(
                    target=module_name, items=items, absorb=absorb, mdl_alias=mdl_alias
                )
                self.bytecode = b""
                self.module = module
            else:
                # Handle Jac module import
                if not full_target.endswith(".jac"):
                    full_target += ".jac"

                if mod_bundle:
                    # print("Using mod_bundle")
                    codeobj = mod_bundle.mod_deps[full_target].gen.py_bytecode
                    codeobj = (
                        marshal.loads(codeobj) if isinstance(codeobj, bytes) else None
                    )
                else:
                    gen_dir = path.join(path.dirname(full_target), Con.JAC_GEN_DIR)
                    pyc_file_path = path.join(gen_dir, module_name + ".jbc")
                    if (
                        cachable
                        and path.exists(pyc_file_path)
                        and path.getmtime(pyc_file_path) > path.getmtime(full_target)
                    ):
                        with open(pyc_file_path, "rb") as f:
                            codeobj = marshal.load(f)
                    else:
                        result = compile_jac(full_target, cache_result=cachable)
                        if result.errors_had or not result.ir.gen.py_bytecode:
                            for e in result.errors_had:
                                print(e)
                                logging.error(e)
                            return None
                        else:
                            # print(f"Compilation successful for {module_name}")
                            codeobj = marshal.loads(result.ir.gen.py_bytecode)
                            # print(f"Compiled bytecode for {module_name}: {codeobj}")

                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_target}")

                module = types.ModuleType(module_name)
                module.__file__ = full_target
                module.__name__ = module_name
                module.__package__ = path.dirname(full_target)
                module.__dict__["__jac_mod_bundle__"] = mod_bundle

                with sys_path_context(caller_dir):
                    exec(codeobj, module.__dict__)

                self.bytecode = codeobj
                self.module = module

                # print(f"Program {module_name} loaded successfully.")
                # print(f"Attributes in module {module_name}: {dir(module)}")
        except Exception as e:
            print(f"Failed to load program {module_name}: {e}")


def py_import(
    target: str,
    items: Optional[dict[str, Union[str, bool]]] = None,
    absorb: bool = False,
    mdl_alias: Optional[str] = None,
) -> types.ModuleType:
    """Import a Python module."""
    try:
        target = target.lstrip(".") if target.startswith("..") else target
        imported_module = importlib.import_module(name=target)
        main_module = __import__("__main__")
        if absorb:
            for name in dir(imported_module):
                if not name.startswith("_"):
                    setattr(main_module, name, getattr(imported_module, name))

        elif items:
            for name, alias in items.items():
                try:
                    setattr(
                        main_module,
                        alias if isinstance(alias, str) else name,
                        getattr(imported_module, name),
                    )
                except AttributeError as e:
                    if hasattr(imported_module, "__path__"):
                        setattr(
                            main_module,
                            alias if isinstance(alias, str) else name,
                            importlib.import_module(f"{target}.{name}"),
                        )
                    else:
                        raise e

        else:
            setattr(
                __import__("__main__"),
                mdl_alias if isinstance(mdl_alias, str) else target,
                imported_module,
            )
        return imported_module
    except ImportError as e:
        print(f"Failed to import module {target}")
        raise e


def get_caller_dir(base_path: str) -> str:
    """Get the directory of the caller.

    Args:
        base_path (str): The base path to use.

    Returns:
        str: The directory of the caller.
    """
    if not base_path:
        return getcwd()
    if path.isdir(base_path):
        return base_path
    return path.dirname(base_path)


class JacMachine:
    """Manages the loading and execution of Jac programs."""

    def __init__(self) -> None:
        """Initialize a JacMachine instance."""
        self.loaded_programs: Dict[str, JacProgram] = {}

    def load_program(
        self,
        filename: str,
        base_path: str = "./",
        cachable: bool = True,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = "jac",
        items: Optional[dict[str, Union[str, bool]]] = None,
        absorb: bool = False,
        mdl_alias: Optional[str] = None,
    ) -> JacProgram:
        """Load a Jac program, or return the already loaded instance.

        Args:
            filename (str): The filename of the program.
            base_path (str, optional): The base path to use. Defaults to "./".
            cachable (bool, optional): Whether the program is cachable. Defaults to True.
            override_name (Optional[str], optional): An optional name override for the module. Defaults to None.
            mod_bundle (Optional[Module], optional): An optional module bundle. Defaults to None.
            lng (Optional[str], optional): The language of the module. Defaults to "jac".
            items (Optional[dict[str, Union[str, bool]]]): Optional items to import.
            absorb (bool): Whether to absorb the imported module into the main module.
            mdl_alias (Optional[str]): Optional alias for the module.

        Returns:
            JacProgram: The loaded Jac program.
        """
        module_name = path.splitext(path.basename(filename))[0]
        if module_name in self.loaded_programs:
            return self.loaded_programs[module_name]

        program = JacProgram(
            filename=filename,
            base_path=base_path,
            cachable=cachable,
            override_name=override_name,
            mod_bundle=mod_bundle,
            lng=lng,
            items=items,
            absorb=absorb,
            mdl_alias=mdl_alias,
        )
        self.loaded_programs[module_name] = program
        return program


machine = JacMachine()
