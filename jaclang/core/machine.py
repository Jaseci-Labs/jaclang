"""Jac Machine Module."""

import importlib
import marshal
import threading
import types
from os import getcwd, path
from typing import Dict, Optional

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging

_execution_context = threading.local()


class JacProgram:
    """Represents a Jac program containing bytecode and its associated module."""

    def __init__(self, bytecode: bytes, module: types.ModuleType) -> None:
        """Initialize a JacProgram instance.

        Args:
            bytecode (bytes): The bytecode of the Jac program.
            module (types.ModuleType): The module associated with the bytecode.
        """
        self.bytecode = bytecode
        self.module = module

    def get_bytecode(self) -> bytes:
        """Retrieve the bytecode of the Jac program.

        Returns:
            bytes: The bytecode of the Jac program.
        """
        return self.bytecode

    def get_execution_context(self) -> dict:
        """Get the execution context for the Jac program.

        Returns:
            dict: A dictionary representing the execution context.
        """
        context = {
            "__file__": self.module.__file__,
            "__name__": self.module.__name__,
            "__package__": self.module.__package__,
            "__doc__": self.module.__doc__,
            "__jac_mod_bundle__": self.module.__dict__.get("__jac_mod_bundle__"),
        }
        return context


class JacMachine:
    """Manages the loading and execution of Jac programs."""

    def __init__(self) -> None:
        """Initialize a JacMachine instance."""
        self.loaded_programs: Dict[str, JacProgram] = {}

    def import_and_load(
        self,
        filename: str,
        base_path: str = "./",
        cachable: bool = True,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = "jac",
    ) -> None:
        """Import and load a Jac or Python program.

        Args:
            filename (str): The filename of the program.
            base_path (str, optional): The base path to use. Defaults to "./".
            cachable (bool, optional): Whether the program is cachable. Defaults to True.
            override_name (Optional[str], optional): An optional name override for the module. Defaults to None.
            mod_bundle (Optional[Module], optional): An optional module bundle. Defaults to None.
            lng (Optional[str], optional): The language of the module. Defaults to "jac".
        """
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
                module = importlib.import_module(module_name)
                self.loaded_programs[module_name] = JacProgram(
                    bytecode=b"", module=module
                )
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

                program = JacProgram(bytecode=codeobj, module=module)
                self.loaded_programs[module_name] = program
                # print(f"Program {module_name} loaded successfully.")
                # print(f"Attributes in module {module_name}: {dir(module)}")
        except Exception as e:
            print(f"Failed to load program {module_name}: {e}")

    def run_program(self, module_name: str) -> None:
        """Run a loaded Jac program.

        Args:
            module_name (str): The name of the module to run.
        """
        if program := self.loaded_programs.get(module_name):
            bytecode = program.get_bytecode()
            execution_context = program.get_execution_context()
            _execution_context.value = execution_context

            # Handle Jac module imports
            def jac_import(
                target: str,
                base_path: str,
                mod_bundle: Optional[Module] = None,
                lng: str = "jac",
                **kwargs: dict,
            ) -> types.ModuleType:
                module_name = path.splitext(path.basename(target))[0]
                if lng == "py":
                    module = importlib.import_module(module_name)
                    for item, alias in kwargs.get("items", {}).items():
                        execution_context[alias or item] = getattr(module, item)
                else:
                    dir_path, file_name = path.split(
                        path.join(*(target.split("."))) + ".jac"
                    )
                    caller_dir = get_caller_dir(base_path)
                    full_target = path.normpath(path.join(caller_dir, file_name))
                    self.import_and_load(
                        filename=full_target,
                        base_path=base_path,
                        cachable=True,
                        override_name=None,
                        mod_bundle=mod_bundle,
                        lng=lng,
                    )
                    program = self.loaded_programs.get(module_name)
                    if program:
                        module = program.module
                        # print(f"Attributes in Jac module {module_name}: {dir(module)}")
                        for item, alias in kwargs.get("items", {}).items():
                            execution_context[alias or item] = getattr(module, item)
                return module

            execution_context["__jac_import__"] = jac_import

            try:
                exec(bytecode, execution_context)
            except Exception as e:
                print(f"Execution failed: {e}")
        else:
            print(f"Program {module_name} not found.")


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


machine = JacMachine()
