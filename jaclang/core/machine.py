"""Jac Machine Module."""

import marshal
import types
from os import getcwd, path
from typing import Dict, Optional

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.utils.log import logging


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
        self.loaded_programs: Dict = {}

    def import_and_load(
        self,
        filename: str,
        base_path: str = "./",
        cachable: bool = True,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
    ) -> None:
        """Import and load a Jac program.

        Args:
            filename (str): The filename of the Jac program.
            base_path (str, optional): The base path to use. Defaults to "./".
            cachable (bool, optional): Whether the program is cachable. Defaults to True.
            override_name (Optional[str], optional): An optional name override for the module. Defaults to None.
            mod_bundle (Optional[Module], optional): An optional module bundle. Defaults to None.
        """
        try:
            module_name = path.splitext(path.basename(filename))[0]
            print(f"Filename: {filename}")
            # Determine full target path
            caller_dir = get_caller_dir(base_path)
            full_target = path.normpath(path.join(caller_dir, filename))
            print(f"Full target: {full_target}")

            if mod_bundle:
                print("Using mod_bundle")
                codeobj = mod_bundle.mod_deps[full_target].gen.py_bytecode
                codeobj = marshal.loads(codeobj) if isinstance(codeobj, bytes) else None
            else:
                gen_dir = path.join(caller_dir, Con.JAC_GEN_DIR)
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
                        codeobj = marshal.loads(result.ir.gen.py_bytecode)

            if not codeobj:
                raise ImportError(f"No bytecode found for {full_target}")

            module = types.ModuleType(module_name)
            module.__file__ = full_target
            module.__name__ = module_name
            module.__package__ = path.dirname(module.__name__)
            module.__dict__["__jac_mod_bundle__"] = mod_bundle

            program = JacProgram(bytecode=codeobj, module=module)
            self.loaded_programs[module_name] = program
            print(f"Program {module_name} loaded successfully.")
        except Exception as e:
            print(f"Failed to load program {module_name}: {e}")

    def run_program(self, module_name: str) -> None:
        """Run a loaded Jac program.

        Args:
            module_name (str): The name of the module to run.
        """
        if program := self.loaded_programs.get(module_name):
            print(f"Running program {module_name}...")
            bytecode = program.get_bytecode()
            execution_context = program.get_execution_context()

            # Adding debug statements to check execution context
            print("Execution context:")
            for key, value in execution_context.items():
                print(f"{key}: {value}")

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
    caller_dir = base_path if path.isdir(base_path) else path.dirname(base_path)
    return caller_dir if caller_dir else getcwd()


machine = JacMachine()
