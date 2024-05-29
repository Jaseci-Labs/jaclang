"""JAC Code for Import."""

import importlib.util
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
        items: Optional[Dict[str, Union[str, bool]]] = None,
        absorb: bool = False,
        mdl_alias: Optional[str] = None,
        jac_machine: Optional["JacMachine"] = None,
    ) -> None:
        """Initialize a JacProgram instance."""
        self.bytecode: Optional[bytes] = None
        self.module: Optional[types.ModuleType] = None
        self.jac_machine = jac_machine
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
        items: Optional[Dict[str, Union[str, bool]]],
        absorb: bool,
        mdl_alias: Optional[str],
    ) -> None:
        """Load the Jac program from a file."""
        try:
            # Transform filename into directory and file name components
            dir_path, file_name = path.split(
                path.join(*(filename.split("."))) + (".jac" if lng == "jac" else ".py")
            )
            module_name = path.splitext(file_name)[0]
            package_path = dir_path.replace(path.sep, ".")

            caller_dir = get_caller_dir(filename, base_path, dir_path)
            full_target = path.normpath(path.join(caller_dir, file_name))

            if lng == "py":
                module = py_import(
                    target=filename,
                    caller_dir=caller_dir,
                    items=items,
                    absorb=absorb,
                    mdl_alias=mdl_alias,
                    jac_machine=self.jac_machine,
                )
                self.bytecode = b""
                self.module = module
            else:
                if not full_target.endswith(".jac"):
                    full_target += ".jac"

                if not path.exists(full_target):
                    raise ImportError(f"No such file: {full_target}")

                if mod_bundle:
                    codeobj = mod_bundle.mod_deps[full_target].gen.py_bytecode
                    codeobj = (
                        marshal.loads(codeobj) if isinstance(codeobj, bytes) else None
                    )
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
                            return
                        else:
                            codeobj = marshal.loads(result.ir.gen.py_bytecode)
                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_target}")
                module = create_jac_py_module(
                    mod_bundle,
                    module_name,
                    package_path,
                    full_target,
                    jac_machine=self.jac_machine,
                )
                with sys_path_context(path.dirname(full_target)):
                    exec(codeobj, module.__dict__)

                self.bytecode = codeobj
                self.module = module

                if self.jac_machine:
                    self.jac_machine.loaded_programs[module_name] = module
                    print(f"Jac program registered: {module_name}")

        except Exception as e:
            print(f"Failed to load program {module_name}: {e}")

    def get_bytecode(self) -> bytes:
        """Retrieve the bytecode of the Jac program.

        Returns:
            bytes: The bytecode of the Jac program.
        """
        return self.bytecode or b""

    def get_execution_context(self) -> dict:
        """Get the execution context for the Jac program.

        Returns:
            dict: A dictionary representing the execution context.
        """
        context = {
            "__file__": self.module.__file__ if self.module else "",
            "__name__": self.module.__name__ if self.module else "",
            "__package__": self.module.__package__ if self.module else "",
            "__doc__": self.module.__doc__ if self.module else None,
            "__jac_mod_bundle__": (
                self.module.__dict__.get("__jac_mod_bundle__") if self.module else None
            ),
        }
        return context


def create_jac_py_module(
    mod_bundle: Optional[Module],
    module_name: str,
    package_path: str,
    full_target: str,
    jac_machine: Optional["JacMachine"],
) -> types.ModuleType:
    """Create a module."""
    module = types.ModuleType(module_name)
    module.__file__ = full_target
    module.__name__ = module_name
    module.__dict__["__jac_mod_bundle__"] = mod_bundle
    if jac_machine:
        jac_machine.loaded_programs[module_name] = module
        if package_path:
            parts = package_path.split(".")
            for i in range(len(parts)):
                package_name = ".".join(parts[: i + 1])
                if package_name not in jac_machine.loaded_programs:
                    jac_machine.loaded_programs[package_name] = types.ModuleType(
                        package_name
                    )

            setattr(jac_machine.loaded_programs[package_path], module_name, module)
            jac_machine.loaded_programs[f"{package_path}.{module_name}"] = module
    return module


def get_caller_dir(target: str, base_path: str, dir_path: str) -> str:
    """Get the directory of the caller."""
    caller_dir = base_path if path.isdir(base_path) else path.dirname(base_path)
    caller_dir = caller_dir if caller_dir else getcwd()
    chomp_target = target
    if chomp_target.startswith("."):
        chomp_target = chomp_target[1:]
        while chomp_target.startswith("."):
            caller_dir = path.dirname(caller_dir)
            chomp_target = chomp_target[1:]
    caller_dir = path.join(caller_dir, dir_path)
    return caller_dir


def py_import(
    target: str,
    caller_dir: str,
    items: Optional[Dict[str, Union[str, bool]]] = None,
    absorb: bool = False,
    mdl_alias: Optional[str] = None,
    jac_machine: Optional["JacMachine"] = None,
) -> types.ModuleType:
    """Import a Python module."""
    try:
        if target.startswith("."):
            print(f"Importing {target} from {caller_dir}")
            target = target.lstrip(".")
            full_target = path.normpath(path.join(caller_dir, target))
            print(f"Full target path: {full_target}")
            spec = importlib.util.spec_from_file_location(target, full_target + ".py")
            print(f"Spec: {spec}")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if jac_machine:
                    jac_machine.loaded_programs[module.__name__] = module
                print(f"Module registered: {module.__name__}")
                return module
            else:
                raise ImportError(f"Cannot find module {target} at {full_target}")
        else:
            print(f"Importing {target} as a regular module")
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
            if jac_machine:
                jac_machine.loaded_programs[imported_module.__name__] = imported_module
            print(f"Regular module registered: {imported_module.__name__}")
            return imported_module
    except ImportError as e:
        print(f"Failed to import module {target}: {e}")
        raise e


class JacMachine:
    """Manages the loading and execution of Jac programs."""

    def __init__(self) -> None:
        """Initialize a JacMachine instance."""
        self.loaded_programs: Dict[str, Union[types.ModuleType, JacProgram]] = {}

    def load_program(
        self,
        filename: str,
        base_path: str = "./",
        cachable: bool = True,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = "jac",
        items: Optional[Dict[str, Union[str, bool]]] = None,
        absorb: bool = False,
        mdl_alias: Optional[str] = None,
    ) -> Union[types.ModuleType, JacProgram]:
        """Load a Jac program, or return the already loaded instance.

        Args:
            filename (str): The filename of the program.
            base_path (str, optional): The base path to use. Defaults to "./".
            cachable (bool, optional): Whether the program is cachable. Defaults to True.
            override_name (Optional[str], optional): An optional name override for the module. Defaults to None.
            mod_bundle (Optional[Module], optional): An optional module bundle. Defaults to None.
            lng (Optional[str], optional): The language of the module. Defaults to "jac".
            items (Optional[Dict[str, Union[str, bool]]]): Optional items to import.
            absorb (bool): Whether to absorb the imported module into the main module.
            mdl_alias (Optional[str]): Optional alias for the module.

        Returns:
            Union[types.ModuleType, JacProgram]: The loaded Jac program or Python module.
        """
        module_name = path.splitext(path.basename(filename))[0]
        if module_name in self.loaded_programs:
            print(f"Module {module_name} already loaded.")
            return self.loaded_programs[module_name]

        # Create and initialize JacProgram, which will handle loading
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
            jac_machine=self,
        )
        print(f"loaded programs: {self.loaded_programs}")
        # Return the loaded program
        if program.module:
            return program.module
        else:
            return program


machine = JacMachine()
