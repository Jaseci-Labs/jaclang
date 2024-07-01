"""Special Imports for Jac Code."""

from __future__ import annotations

import abc
import importlib
import marshal
import os
import sys
import types
from typing import Dict, Optional, Type, Union

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging


class SysModulesPatch:
    """Context manager to temporarily patch the sys.modules dictionary."""

    def __init__(self, loaded_programs: dict[str, types.ModuleType]) -> None:
        """Initialize the SysModulesPatch context manager with the provided modules."""
        self.loaded_programs = loaded_programs
        self.original_sys_modules: dict[str, types.ModuleType]

    def __enter__(self) -> None:
        """Enter the runtime context and patch sys.modules."""
        self.original_sys_modules = sys.modules.copy()
        sys.modules.update(self.loaded_programs)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> None:
        """Exit the runtime context and restore the original sys.modules."""
        sys.modules.clear()
        sys.modules.update(self.original_sys_modules)


class ImportPathSpec:
    """Handles all import path specifications and related metadata."""

    def __init__(
        self,
        target: str,
        machine: JacMachine,
        absorb: bool = False,
        mdl_alias: Optional[str] = None,
        override_name: Optional[str] = None,
        lng: Optional[str] = "jac",
        items: Optional[Dict[str, Union[str, bool]]] = None,
    ) -> None:
        """Initialize ImportPathSpec."""
        self.target = target
        self.machine = machine
        self.absorb = absorb
        self.mdl_alias = mdl_alias
        self.override_name = override_name or target
        self.language = lng
        self.items = items
        self.full_mod_path = self.get_full_target()
        self.sys_mod_name = (
            override_name if override_name else self.resolve_sys_mod_name()
        )
        # self.sys_mod_name = self.resolve_sys_mod_name()

    def get_full_target(self) -> str:
        """Compute the full file path based on the target and base path."""

        def get_caller_dir(target: str, base_path: str, dir_path: str) -> str:
            """Get the directory of the caller."""
            caller_dir = (
                base_path if os.path.isdir(base_path) else os.path.dirname(base_path)
            )
            caller_dir = caller_dir if caller_dir else os.getcwd()
            chomp_target = target
            if chomp_target.startswith("."):
                chomp_target = chomp_target[1:]
                while chomp_target.startswith("."):
                    caller_dir = os.path.dirname(caller_dir)
                    chomp_target = chomp_target[1:]
            caller_dir = os.path.join(caller_dir, dir_path)
            return caller_dir

        def smart_join(base_path: str, target_path: str) -> str:
            """Join two paths while attempting to remove any redundant segments."""
            base_parts = os.path.normpath(base_path).split(os.sep)
            target_parts = os.path.normpath(target_path).split(os.sep)
            while base_parts and target_parts and base_parts[-1] == target_parts[0]:
                target_parts.pop(0)
            return os.path.normpath(os.path.join(base_path, *target_parts))

        target_path = os.path.join(*(self.target.split(".")))
        dir_path, file_name = os.path.split(target_path)
        self.caller_dir = get_caller_dir(self.target, self.machine.base_path, dir_path)
        self.module_name = os.path.splitext(file_name)[0]
        return smart_join(self.caller_dir, target_path)

    def resolve_sys_mod_name(self, full_path: Optional[str] = None) -> str:
        """Resolve system module name from the full path of a file and the base module path."""
        full_path = (
            os.path.abspath(self.full_mod_path) if full_path is None else full_path
        )
        if full_path is not None and not full_path.startswith(
            self.machine.main_base_dir
        ):
            return ""
        rel_path = os.path.relpath(full_path, self.machine.main_base_dir)
        if rel_path.endswith(".jac"):
            rel_path = rel_path[:-4]
        mod_name = rel_path.replace(os.sep, ".").strip(".")
        if mod_name.endswith(".__init__"):
            mod_name = mod_name[:-9]
        return mod_name


class Importer(abc.ABC):
    """Abstract base class for all types of module importers."""

    @abc.abstractmethod
    def run_import(self, spec: ImportPathSpec) -> ImportReturn:
        """Implement import logic as specified by subclasses."""
        raise NotImplementedError("Subclasses must implement this method.")

    @abc.abstractmethod
    def update_sys(self, module: types.ModuleType, spec: "ImportPathSpec") -> None:
        """Update system configuration as necessary."""
        raise NotImplementedError("Subclasses must implement this method.")

    def log_error(self, message: str) -> None:
        """Log an error message."""
        raise ImportError(message)

    # @abc.abstractmethod
    # def ensure_parent_module(
    #     self, module_name: str, full_target: str, mod_bundle: types.ModuleType
    # ) -> types.ModuleType:
    #     pass

    # @abc.abstractmethod
    # def load_jac_file(
    #     self,
    #     module: types.ModuleType,
    #     name: str,
    #     jac_file_path: str,
    #     spec: ImportPathSpec,
    # ) -> types.ModuleType | None:
    #     pass

    def validate_spec(self, spec: ImportPathSpec) -> None:
        """Validate the provided ImportPathSpec."""
        if not spec.module_name or not spec.full_mod_path:
            raise ImportError("Specification missing required module name or path.")


class ImportReturn:
    """Handles the return of processed modules and their items."""

    def __init__(
        self,
        module: types.ModuleType,
        spec: ImportPathSpec,
        importer: Importer,
    ) -> None:
        """Initialize the import return module."""
        self.ret_mod = module
        self.importer = importer
        self.spec = spec
        (self.ret_mod, self.ret_list) = self.decide_return(module, spec)

    def setup_parent_modules(self, spec: ImportPathSpec) -> None:
        """Set up and register parent modules for the current module."""
        parent_module_name, submodule_name = spec.target.rsplit(".", 1)
        if isinstance(self.importer, JacImporter):
            parent_module = self.importer.ensure_parent_module(
                parent_module_name, spec.full_mod_path, self.spec.machine.mod_bundle
            )
        setattr(parent_module, submodule_name, self.ret_mod)
        self.parent_module = parent_module

    def get_module_directory(self, module: types.ModuleType) -> str:
        """Get the directory of the module."""
        if hasattr(module, "__path__"):
            return module.__path__[0]
        elif hasattr(module, "__file__"):
            return (
                os.path.dirname(module.__file__) if module.__file__ is not None else ""
            )
        return ""

    def get_attribute_or_import(
        self, module: types.ModuleType, name: str, module_dir: str, spec: ImportPathSpec
    ) -> Optional[types.ModuleType]:
        """Attempt to get an attribute from the module; if it's missing, try to import it."""
        try:
            return getattr(module, name)
        except AttributeError:
            return self.import_missing_item(module, name, module_dir, spec)

    def import_missing_item(
        self, module: types.ModuleType, name: str, module_dir: str, spec: ImportPathSpec
    ) -> Optional[types.ModuleType]:
        """Import a missing item from the file system or handle language-specific imports."""
        jac_file_path = os.path.join(module_dir, f"{name}.jac")

        if spec.language == "jac" and os.path.isfile(jac_file_path):
            return (
                self.importer.load_jac_file(module, name, jac_file_path, spec)
                if isinstance(self.importer, JacImporter)
                else None
            )
        elif spec.language == "py":
            return self.import_py_module(module, name)
        return None

    def import_py_module(
        self, module: types.ModuleType, name: str
    ) -> Optional[types.ModuleType]:
        """Import a Python module as an attribute of another module."""
        if hasattr(module, "__path__"):
            full_module_name = f"{module.__name__}.{name}"
            return importlib.import_module(full_module_name)
        return None

    def assign_alias(
        self,
        module: types.ModuleType,
        original_name: str,
        alias: Union[str, bool],
        item: types.ModuleType,
    ) -> None:
        """Assign an alias to the item in the module, if necessary."""
        if isinstance(alias, bool) and alias:
            alias = original_name
        if alias and alias != original_name:
            setattr(module, alias, item)

    def process_items(
        self,
        module: types.ModuleType,
        items: Dict[str, Union[str, bool]],
        spec: ImportPathSpec,
    ) -> list:
        """Process items within a module by handling renaming and potentially loading missing attributes."""
        unique_loaded_items = []
        module_dir = self.get_module_directory(module)

        for name, alias in items.items():
            item = self.get_attribute_or_import(module, name, module_dir, spec)
            if item:
                unique_loaded_items.append(item)
                self.assign_alias(
                    module=module, original_name=name, alias=alias, item=item
                )

        return unique_loaded_items

    def decide_return(self, module: types.ModuleType, spec: ImportPathSpec) -> tuple:
        """Decides whether to return just the module or the processed items based on spec."""
        processed_items = []
        if "." in spec.target and spec.language == "jac":
            self.setup_parent_modules(spec)
            if spec.items:
                processed_items = self.process_items(module, spec.items, spec)
            if spec.absorb or not processed_items:
                return (self.parent_module, []) if not spec.mdl_alias else (module, [])
            else:
                return (None, processed_items)
        if spec.items:
            processed_items = self.process_items(module, spec.items, spec)
            return (None, processed_items)
        return (module, [])


class JacImporter(Importer):
    """Jac Importer class."""

    def __init__(self, machine: JacMachine) -> None:
        """Initialize JacImporter."""
        self.machine = machine

    def ensure_parent_module(
        self, module_name: str, full_target: str, mod_bundle: Optional[types.ModuleType]
    ) -> types.ModuleType:
        """Ensure that the module is created and added to loaded_programs."""
        try:
            if module_name in self.machine.loaded_programs:
                module = self.machine.loaded_programs[module_name]
            else:
                module = types.ModuleType(module_name)
                module.__dict__["__jac_mod_bundle__"] = mod_bundle
                self.machine.loaded_programs[module_name] = module
            module_directory = os.path.dirname(full_target)
            if os.path.isdir(module_directory):
                module.__path__ = [module_directory]
            parent_name, _, child_name = module_name.rpartition(".")
            if parent_name:
                parent_module = self.ensure_parent_module(
                    parent_name, module_directory, mod_bundle
                )
                setattr(parent_module, child_name, module)
            return module
        except Exception as e:
            raise ImportError(f"Error creating module {module_name}: {e}") from e

    def load_jac_file(
        self,
        module: types.ModuleType,
        name: str,
        jac_file_path: str,
        spec: ImportPathSpec,
    ) -> types.ModuleType | None:
        """Load a single .jac file into the specified module component."""
        try:
            package_name = (
                f"{module.__name__}.{name}"
                if hasattr(module, "__path__")
                else module.__name__
            )
            new_module = self.machine.loaded_programs.get(
                package_name, self.create_jac_py_module(spec, name, jac_file_path)
            )

            codeobj = self.get_codeobj(
                full_target=jac_file_path,
                module_name=name,
                mod_bundle=self.machine.mod_bundle,
                cachable=self.machine.cachable,
            )
            if not codeobj:
                raise ImportError(f"No bytecode found for {jac_file_path}")

            exec(codeobj, new_module.__dict__)
            return getattr(new_module, name, new_module)
        except ImportError as e:
            self.log_error(f"Failed to load {name} from {jac_file_path}: {str(e)}")
            return None

    def run_import(self, spec: ImportPathSpec) -> ImportReturn:
        """Import a Jac module using the specifications provided."""
        self.validate_spec(spec)
        full_jac_path = f"{spec.full_mod_path}.jac"
        if os.path.isdir(spec.full_mod_path):
            module = self.handle_directory(spec)

        else:
            if os.path.isfile(full_jac_path):
                module = self.create_jac_py_module(spec)
            else:
                path_parts = spec.full_mod_path.rsplit("/", 1)
                if len(path_parts) > 1:
                    modified_path = path_parts[0] + "." + path_parts[1]
                    full_jac_path = f"{modified_path}.jac"
                    if os.path.isfile(full_jac_path):
                        spec.full_mod_path = modified_path
                        module = self.create_jac_py_module(spec)
                    else:
                        self.log_error(f"No file found at {spec.full_mod_path}.jac")
                else:
                    self.log_error(f"No file found at {spec.full_mod_path}.jac")
            codeobj = self.get_codeobj(
                full_target=full_jac_path,
                module_name=module.__name__,
                mod_bundle=self.machine.mod_bundle,
                cachable=self.machine.cachable,
            )
            if not codeobj:
                self.log_error(f"No bytecode found for {spec.full_mod_path}")
            else:
                with SysModulesPatch(self.machine.loaded_programs), sys_path_context(
                    os.path.dirname(spec.full_mod_path)
                ):
                    module.__file__ = f"{spec.full_mod_path}.jac"
                    exec(codeobj, module.__dict__)

        return ImportReturn(module, spec=spec, importer=self)

    def get_codeobj(
        self,
        full_target: str,
        module_name: str,
        mod_bundle: Optional[Module],
        cachable: bool,
    ) -> Optional[types.CodeType]:
        """Execcutes the code for a given module."""
        if mod_bundle and isinstance(mod_bundle, Module):
            get_mod = mod_bundle.mod_deps.get(full_target)
            codeobj = get_mod.gen.py_bytecode if get_mod else None
            if codeobj and isinstance(codeobj, bytes):
                return marshal.loads(codeobj)
        gen_dir = os.path.join(os.path.dirname(full_target), Con.JAC_GEN_DIR)
        pyc_file_path = os.path.join(gen_dir, module_name + ".jbc")
        if cachable and os.path.exists(pyc_file_path):
            with open(pyc_file_path, "rb") as f:
                return marshal.load(f)

        result = compile_jac(full_target, cache_result=cachable)
        if result.errors_had or not result.ir.gen.py_bytecode:
            for e in result.errors_had:
                logging.error(e)
            return None
        return marshal.loads(result.ir.gen.py_bytecode)

    def create_jac_py_module(
        self,
        spec: ImportPathSpec,
        module_name: str = "",
        full_target: str = "",
    ) -> types.ModuleType:
        """Create a module and ensure all parent namespaces are registered in sys.modules."""
        if not module_name and not full_target:
            module = self.machine.loaded_programs.get(
                f"{self.machine.main_base_dir}.{spec.module_name}"
                if self.machine.main_base_dir
                else spec.module_name
            )
        else:
            module = None
            spec.sys_mod_name = ""
        if not full_target:
            if not os.path.isdir(spec.full_mod_path):
                full_target = f"{spec.full_mod_path}.jac"
            else:
                full_target = spec.full_mod_path
        if not module:
            if spec.sys_mod_name:
                module_name = spec.sys_mod_name
            else:
                module_name = spec.resolve_sys_mod_name(full_target)
            module = types.ModuleType(module_name)
            module.__name__ = module_name
            module.__dict__["__jac_mod_bundle__"] = self.machine.mod_bundle
            if os.path.isdir(full_target):
                module.__path__ = [full_target]
                init_file = os.path.join(full_target, "__init__.jac")
                if os.path.isfile(init_file):
                    module.__file__ = init_file
            else:
                module.__file__ = full_target

            namespace_parts = module_name.split(".")
            constructed_path = ""
            for i, part in enumerate(namespace_parts):
                constructed_path = (
                    f"{constructed_path}.{part}" if constructed_path else part
                )
                if constructed_path not in self.machine.loaded_programs:
                    interim_module = types.ModuleType(constructed_path)
                    interim_module.__package__ = ".".join(
                        constructed_path.split(".")[:-1]
                    )
                    interim_module.__dict__["__jac_mod_bundle__"] = (
                        self.machine.mod_bundle
                    )
                    if os.path.isdir(os.path.dirname(full_target)):
                        interim_module.__path__ = [os.path.dirname(full_target)]
                    if i == len(namespace_parts) - 1 and not os.path.isdir(full_target):
                        interim_module.__file__ = module.__file__
                    self.machine.loaded_programs[constructed_path] = interim_module
                if i > 0:
                    parent_path = ".".join(namespace_parts[:i])
                    parent_module = self.machine.loaded_programs[parent_path]
                    setattr(
                        parent_module,
                        part,
                        self.machine.loaded_programs[constructed_path],
                    )

        return module

    def update_sys(self, module: types.ModuleType, spec: "ImportPathSpec") -> None:
        """Update sys.modules after import."""
        if spec.module_name not in self.machine.loaded_programs:
            self.machine.loaded_programs[spec.sys_mod_name] = module

    def handle_directory(self, spec: ImportPathSpec) -> types.ModuleType:
        """Import from a directory that potentially contains multiple Jac modules."""
        module = self.create_jac_py_module(spec)
        init_file_py = os.path.join(spec.full_mod_path, "__init__.py")
        init_file_jac = os.path.join(spec.full_mod_path, "__init__.jac")
        if os.path.exists(init_file_py):
            self.exec_init_file(init_file_py, module, spec.caller_dir)
        elif os.path.exists(init_file_jac):
            self.exec_init_file(init_file_jac, module, spec.caller_dir)
        self.update_sys(module, spec)
        return module

    def exec_init_file(
        self, init_file: str, module: types.ModuleType, caller_dir: str
    ) -> None:
        """Execute the initialization file specified by `init_file`."""
        if init_file.endswith(".py"):
            spec = importlib.util.spec_from_file_location(module.__name__, init_file)
            if spec and spec.loader:
                self.machine.loaded_programs[module.__name__] = (
                    importlib.util.module_from_spec(spec)
                )
                spec.loader.exec_module(module)
        elif init_file.endswith(".jac"):
            codeobj = self.get_codeobj(
                full_target=init_file,
                module_name=module.__name__,
                mod_bundle=module.__dict__["__jac_mod_bundle__"],
                cachable=True,
            )
            if codeobj:
                with sys_path_context(caller_dir):
                    exec(codeobj, module.__dict__)
            else:
                self.log_error(f"Failed to compile or execute Jac code in {init_file}")


class PythonImporter(Importer):
    """Python importer."""

    def __init__(self, machine: JacMachine) -> None:
        """Initialize PythonImporter."""
        self.machine = machine

    def run_import(self, spec: ImportPathSpec) -> ImportReturn:
        """Import a Python module using the specifications provided."""
        self.validate_spec(spec)

        try:
            loaded_items = {}
            if spec.target.startswith("."):
                spec.target = spec.target.lstrip(".")
                full_target = os.path.normpath(
                    os.path.join(spec.caller_dir, spec.target)
                )
                module_spec = importlib.util.spec_from_file_location(
                    spec.target, full_target + ".py"
                )
                if module_spec and module_spec.loader:
                    module = importlib.util.module_from_spec(module_spec)
                    module_spec.loader.exec_module(module)
                else:
                    raise ImportError(
                        f"Cannot find module {spec.target} at {full_target}"
                    )
            else:
                module = importlib.import_module(name=spec.target)

            # Now update sys.modules as part of the import process
            self.update_sys(module, spec)

            main_module = __import__("__main__")

            if spec.absorb:
                for name in dir(module):
                    if not name.startswith("_"):
                        setattr(main_module, name, getattr(module, name))

            elif spec.items:
                for name, alias in spec.items.items():
                    if isinstance(alias, bool):
                        alias = name
                    item = getattr(module, name, None)
                    if item:
                        setattr(
                            main_module, alias if isinstance(alias, str) else name, item
                        )
                        loaded_items[alias if isinstance(alias, str) else name] = item

            else:
                if spec.mdl_alias:
                    setattr(main_module, spec.mdl_alias, module)
                else:
                    setattr(main_module, spec.target, module)
            return ImportReturn(module, spec, importer=self)
        except ImportError as e:
            self.log_error(str(e))
            raise e

    def update_sys(self, module: types.ModuleType, spec: "ImportPathSpec") -> None:
        """Update sys.modules after import."""
        if spec.module_name not in self.machine.loaded_programs:
            self.machine.loaded_programs[spec.sys_mod_name] = module


class JacMachine:
    """Manages the loading and execution of Jac programs."""

    def __init__(self, base_path: str) -> None:
        """Initialize a JacMachine instance."""
        self.loaded_programs: dict = {}
        self.importers = {"jac": JacImporter(self), "py": PythonImporter(self)}
        self.main_base_dir = self.initialize_base_dir(base_path)
        self.cachable = True
        self.mod_bundle = None
        self.base_path = base_path

    def run(
        self,
        target: str,
        base_path: str,
        absorb: bool = False,
        cachable: bool = True,
        mdl_alias: Optional[str] = None,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module | str] = None,
        lng: Optional[str] = "jac",
        items: Optional[dict[str, Union[str, bool]]] = None,
    ) -> Optional[tuple[types.ModuleType, ...] | None]:
        """Load a module based on provided parameters, handling Jac and Python specifics."""
        self.cachable = cachable
        valid_mod_bundle = (
            self.loaded_programs[mod_bundle].__jac_mod_bundle__
            if isinstance(mod_bundle, str)
            and mod_bundle in self.loaded_programs
            and "__jac_mod_bundle__" in self.loaded_programs[mod_bundle].__dict__
            else mod_bundle
        )
        self.base_path = base_path
        self.mod_bundle = valid_mod_bundle
        spec = ImportPathSpec(
            target=target,
            machine=self,
            absorb=absorb,
            mdl_alias=mdl_alias,
            override_name=override_name,
            lng=lng,
            items=items,
        )
        importer = self.importers[lng if lng is not None else "jac"]
        import_result = importer.run_import(spec)

        if import_result.ret_mod:
            self.loaded_programs[spec.module_name] = import_result.ret_mod
            return (import_result.ret_mod,)

        return tuple(import_result.ret_list if import_result.ret_list else [])

    def initialize_base_dir(self, base_path: str) -> str:
        """Compute and set the main base directory."""
        if not os.path.isdir(base_path):
            return os.path.dirname(base_path)
        elif os.path.isfile(base_path):
            return base_path
        else:
            return os.path.abspath(base_path)
