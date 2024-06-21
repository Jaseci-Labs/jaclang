import abc
import os
import importlib
import marshal
import os
import sys
import types
from typing import Optional, Union, Dict

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging


class ImportPathSpec:
    """Handles all import path specifications and related metadata."""

    main_base_dir: str = None

    def __init__(
        self,
        target: str,
        base_path: str,
        absorb: bool = False,
        cachable: bool = True,
        mdl_alias: Optional[str] = None,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: str = "jac",
        items: Optional[Dict[str, Union[str, bool]]] = None,
    ):
        self.target = target
        self.base_path = base_path
        self.absorb = absorb
        self.cachable = cachable
        self.mdl_alias = mdl_alias
        self.override_name = override_name or target
        self.mod_bundle = mod_bundle
        self.language = lng
        self.items = items
        self.set_main_base_dir()
        self.full_mod_path = self.get_full_target()
        self.sys_mod_name = self.resolve_sys_mod_name()

    def set_main_base_dir(self):
        """Compute and set the main base directory"""
        if ImportPathSpec.main_base_dir is None:
            if not os.path.isdir(self.base_path):
                ImportPathSpec.main_base_dir = os.path.dirname(self.base_path)
            else:
                ImportPathSpec.main_base_dir = self.base_path

    def get_main_base_dir(cls):
        """Retrieve the main base directory"""
        return cls.main_base_dir

    def get_full_target(self) -> str:
        """Computes the full file path based on the target and base path."""
        target_path = os.path.join(*(self.target.split(".")))
        dir_path, file_name = os.path.split(target_path)
        self.caller_dir = self.get_caller_dir(self.target, self.base_path, dir_path)
        full_target = os.path.normpath(os.path.join(self.caller_dir, target_path))
        self.module_name = os.path.splitext(file_name)[0]
        return self.smart_join(self.caller_dir, target_path)

    def resolve_sys_mod_name(self, full_path=None) -> str:
        """Resolve system module name from the full path of a file and the base module path."""
        full_path = (
            os.path.abspath(self.full_mod_path) if full_path is None else full_path
        )
        if not full_path.startswith(ImportPathSpec.main_base_dir):
            return None
        rel_path = os.path.relpath(full_path, ImportPathSpec.main_base_dir)
        if rel_path.endswith(".jac"):
            rel_path = rel_path[:-4]
        mod_name = rel_path.replace(os.sep, ".").strip(".")
        if mod_name.endswith(".__init__"):
            mod_name = mod_name[:-9]  # Remove the '.__init__' suffix
        return mod_name

    def smart_join(self, base_path: str, target_path: str) -> str:
        """Join two paths while attempting to remove any redundant segments."""
        base_parts = os.path.normpath(base_path).split(os.sep)
        target_parts = os.path.normpath(target_path).split(os.sep)
        while base_parts and target_parts and base_parts[-1] == target_parts[0]:
            target_parts.pop(0)
        return os.path.normpath(os.path.join(base_path, *target_parts))

    def get_caller_dir(self, target: str, base_path: str, dir_path: str) -> str:
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


class Importer(abc.ABC):
    """Abstract base class for all types of module importers."""

    @abc.abstractmethod
    def run_import(self, spec: "ImportPathSpec") -> "ImportReturn":
        """
        Executes the import process based on the specifications provided.
        This method must be implemented by all subclasses to handle specific import logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abc.abstractmethod
    def update_sys(self, spec: "ImportPathSpec"):
        """
        Updates sys.modules or any other necessary system-level configurations.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def log_error(self, message: str):
        """
        Logs an error message. This can be overridden by subclasses if they have specific logging requirements.
        """
        print(
            f"Error: {message}"
        )  # Placeholder for logging, can be replaced with a proper logging framework.

    def validate_spec(self, spec: "ImportPathSpec") -> bool:
        """
        Validates the provided ImportPathSpec to ensure it meets the requirements for processing.
        This is a utility method that can be used by subclasses before processing begins.
        """
        # Example validation, can be expanded based on actual requirements
        if not spec.module_name or not spec.full_mod_path:
            self.log_error("Specification missing required module name or path.")
            return False
        return True


class ImportReturn:
    """Handles the return of processed modules and their items."""

    def __init__(
        self,
        module: types.ModuleType,
        items: dict,
        spec: ImportPathSpec,
        mod_bundle: Module,
        importer: Importer = None,
    ):

        self.ret_mod = module
        self.mod_bundle = mod_bundle
        self.importer = importer
        (self.ret_mod, self.ret_list) = self.decide_return(module, spec)

    def setup_parent_modules(self, spec):
        """Handles setting up and registering parent modules for the current module."""
        parent_module_name, submodule_name = spec.target.rsplit(".", 1)
        parent_module = self.importer.ensure_parent_module(
            parent_module_name, spec.full_mod_path, self.mod_bundle
        )
        setattr(parent_module, submodule_name, self.ret_mod)
        self.parent_module = parent_module

    def process_items(self, module, items, mod_bundle, spec):
        """Processes items in a module, handling renaming and importing missing attributes."""

        unique_loaded_items = []
        if not items:
            return unique_loaded_items
        if spec.language == "jac":
            module_dir = (
                module.__path__[0]
                if hasattr(module, "__path__")
                else os.path.dirname(module.__file__)
            )

        for name, alias in items.items():
            try:
                item = getattr(module, name)
                unique_loaded_items.append(item)
                if alias and alias != name:
                    setattr(module, alias, item)
            except AttributeError:
                jac_file_path = os.path.join(module_dir, f"{name}.jac")
                if hasattr(module, "__path__") and os.path.isfile(jac_file_path):
                    item = self.importer.load_jac_file(
                        module, name, jac_file_path, spec
                    )
                    if item:
                        setattr(module, name, item)
                        unique_loaded_items.append(item)
                        if alias and alias != name:
                            setattr(module, alias, item)
                elif spec.language == "py":
                    if hasattr(module, "__path__"):
                        item = importlib.import_module(f"{module.__name__}.{name}")
                        if item not in unique_loaded_items:
                            unique_loaded_items.append(item)
                else:
                    # Attempt to load the item from the module's file directly
                    jac_file_path = module.__file__
                    if os.path.isfile(jac_file_path):
                        item = self.importer.load_jac_file(
                            module, name, jac_file_path, spec
                        )
                        if item:
                            setattr(module, name, item)
                            unique_loaded_items.append(item)
                            if alias and alias != name:
                                setattr(module, alias, item)

        return unique_loaded_items

    def decide_return(self, module, spec):
        """Decides whether to return just the module or the processed items based on spec."""
        processed_items = []
        if "." in spec.target and spec.language == "jac":
            self.setup_parent_modules(spec)
            if spec.items:
                processed_items = self.process_items(
                    module, spec.items, spec.mod_bundle, spec
                )
            if spec.absorb or not processed_items:
                return (
                    (self.parent_module, None) if not spec.mdl_alias else (module, None)
                )
            else:
                return (None, processed_items)
        if spec.items:
            processed_items = self.process_items(
                module, spec.items, spec.mod_bundle, spec
            )
            return (None, processed_items)
        return (module, None)


class JacImporter(Importer):
    def ensure_parent_module(self, module_name, full_target, mod_bundle):
        """Ensure that the parent module is properly set up in sys.modules."""
        if module_name in sys.modules:
            return sys.modules[module_name]

        parent_name, _, child_name = module_name.rpartition(".")
        if parent_name:
            parent_module = self.ensure_parent_module(
                parent_name, os.path.dirname(full_target), mod_bundle
            )
        else:
            parent_module = types.ModuleType(module_name)
            parent_module.__dict__["__path__"] = [os.path.dirname(full_target)]
            parent_module.__dict__["__jac_mod_bundle__"] = mod_bundle
            sys.modules[module_name] = parent_module

        return parent_module

    def load_jac_file(self, module, name, jac_file_path, spec):
        """Loads a single .jac file as a module component."""
        try:
            package_name = (
                f"{module.__name__}.{name}"
                if hasattr(module, "__path__")
                else module.__name__
            )
            if package_name not in sys.modules:
                new_module = self.create_jac_py_module(spec, name, jac_file_path)
            else:
                new_module = sys.modules[package_name]

            codeobj = self.get_codeobj(
                jac_file_path, name, spec.mod_bundle, spec.cachable
            )
            if not codeobj:
                raise ImportError(f"No bytecode found for {jac_file_path}")

            exec(codeobj, new_module.__dict__)
            return getattr(new_module, name, new_module)
        except ImportError as e:
            self.log_error(f"Failed to load {name} from {jac_file_path}: {str(e)}")
            return None

    def run_import(self, spec: "ImportPathSpec") -> "ImportReturn":
        """Import a Jac module using the specifications provided."""
        if not self.validate_spec(spec):
            return ImportReturn(None, {})
        if os.path.isdir(spec.full_mod_path):
            module = self.handle_directory(spec)
        else:
            module = self.create_jac_py_module(spec)
            # spec.mod_bundle,
            # spec.override_name if spec.override_name else spec.module_name,
            # spec.main_base_dir,  # This would typically be package_path in context.
            # f"{spec.full_mod_path}.jac",
            # spec.sys_mod_name,
            # )

            codeobj = self.get_codeobj(
                f"{spec.full_mod_path}.jac",
                module.__name__,
                spec.mod_bundle,
                spec.cachable,
            )
            if not codeobj:
                self.log_error(f"No bytecode found for {spec.full_mod_path}")
                return ImportReturn(None, {})

            with sys_path_context(os.path.dirname(spec.full_mod_path)):
                module.__file__ = f"{spec.full_mod_path}.jac"
                exec(codeobj, module.__dict__)

        return ImportReturn(
            module, {}, mod_bundle=spec.mod_bundle, spec=spec, importer=self
        )

    def get_codeobj(
        self,
        full_target: str,
        module_name: str,
        mod_bundle: Optional[types.ModuleType],
        cachable: bool,
    ) -> Optional[types.CodeType]:
        if mod_bundle:
            codeobj = mod_bundle.mod_deps.get(full_target, {}).gen.py_bytecode
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
        spec: "ImportPathSpec",
        # mod_bundle: Optional[Module],
        module_name: str = None,
        # package_path: str,
        full_target: str = None,
        # sys_mod_name: str,
    ) -> types.ModuleType:
        """Create a module and ensure all parent namespaces are registered in sys.modules."""
        if not module_name and not full_target:
            module = sys.modules.get(
                f"{spec.main_base_dir}.{spec.module_name}"
                if spec.main_base_dir
                else spec.module_name
            )
        else:
            module = None
            spec.sys_mod_name = None
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
            module.__dict__["__jac_mod_bundle__"] = spec.mod_bundle
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
                if constructed_path not in sys.modules:
                    interim_module = types.ModuleType(constructed_path)
                    interim_module.__package__ = ".".join(
                        constructed_path.split(".")[:-1]
                    )
                    interim_module.__dict__["__jac_mod_bundle__"] = spec.mod_bundle
                    if os.path.isdir(os.path.dirname(full_target)):
                        interim_module.__path__ = [os.path.dirname(full_target)]
                    if i == len(namespace_parts) - 1 and not os.path.isdir(full_target):
                        interim_module.__file__ = module.__file__
                    sys.modules[constructed_path] = interim_module
                if i > 0:
                    parent_path = ".".join(namespace_parts[:i])
                    parent_module = sys.modules[parent_path]
                    setattr(parent_module, part, sys.modules[constructed_path])

        return module

    def update_sys(self, module: types.ModuleType, spec: "ImportPathSpec"):
        """Update sys.modules after import."""
        if spec.module_name not in sys.modules:
            sys.modules[spec.sys_mod_name] = module

    def handle_directory(self, spec: "ImportPathSpec") -> "ImportReturn":
        """Handles importing from a directory, potentially containing multiple Jac modules."""
        full_target = spec.full_mod_path
        module_name = (
            spec.override_name
            if spec.override_name
            else os.path.splitext(os.path.basename(full_target))[0]
        )
        package_path = os.path.dirname(full_target).replace(os.sep, ".")
        module = self.create_jac_py_module(spec)
        # Execute __init__ file if present
        init_file_py = os.path.join(full_target, "__init__.py")
        init_file_jac = os.path.join(full_target, "__init__.jac")
        if os.path.exists(init_file_py):
            self.exec_init_file(init_file_py, module, spec.caller_dir)
        elif os.path.exists(init_file_jac):
            self.exec_init_file(init_file_jac, module, spec.caller_dir)
        # Update sys.modules and return the module wrapped in ImportReturn
        self.update_sys(module, spec)
        return module

    def exec_init_file(self, init_file: str, module: types.ModuleType, caller_dir: str):
        """Executes an initialization file to setup a package module."""
        if init_file.endswith(".py"):
            spec = importlib.util.spec_from_file_location(module.__name__, init_file)
            if spec and spec.loader:
                sys.modules[module.__name__] = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        elif init_file.endswith(".jac"):
            codeobj = self.get_codeobj(
                init_file, module.__name__, module.__dict__["__jac_mod_bundle__"], True
            )
            if codeobj:
                with sys_path_context(caller_dir):
                    exec(codeobj, module.__dict__)
            else:
                self.log_error(f"Failed to compile or execute Jac code in {init_file}")


class PythonImporter(Importer):
    def run_import(self, spec: "ImportPathSpec") -> "ImportReturn":
        """Import a Python module using the specifications provided."""
        if not self.validate_spec(spec):
            return ImportReturn(None, {})

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
            return ImportReturn(module, spec.items, spec, mod_bundle=None)
        except ImportError as e:
            self.log_error(str(e))
            return ImportReturn(None, {})

    def update_sys(self, module: types.ModuleType, spec: "ImportPathSpec"):
        """Update sys.modules after import."""
        if spec.module_name not in sys.modules:
            sys.modules[spec.sys_mod_name] = module


def jac_importer(
    target: str,
    base_path: str,
    absorb: bool = False,
    cachable: bool = True,
    mdl_alias: Optional[str] = None,
    override_name: Optional[str] = None,
    mod_bundle: Optional[Module] = None,
    lng: Optional[str] = "jac",
    items: Optional[dict[str, Union[str, bool]]] = None,
) -> Optional[tuple[Module, ...]]:
    spec = ImportPathSpec(
        target=target,
        base_path=base_path,
        absorb=absorb,
        cachable=cachable,
        mdl_alias=mdl_alias,
        override_name=override_name,
        mod_bundle=mod_bundle,
        lng=lng,
        items=items,
    )
    if spec.language == "py":
        importer = PythonImporter()
    else:
        importer = JacImporter()
    data = importer.run_import(spec)
    if data.ret_mod:
        return (data.ret_mod,)
    return tuple(data.ret_list)
