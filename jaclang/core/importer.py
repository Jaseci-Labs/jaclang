"""Special Imports for Jac Code."""

import importlib
import marshal
import os
import sys
import types
from os import getcwd, path
from typing import Optional, Union

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging


def smart_join(base_path: str, target_path: str) -> str:
    """Join two paths while attempting to remove any redundant segments."""
    base_parts = path.normpath(base_path).split(path.sep)
    target_parts = path.normpath(target_path).split(path.sep)

    # Attempt to detect and remove overlapping segments
    while base_parts and target_parts and base_parts[-1] == target_parts[0]:
        target_parts.pop(0)

    full_path = path.join(base_path, *target_parts)
    return path.normpath(full_path)


def process_items(module, items, target):
    """Extracts items from a module, renaming them if specified, and handles missing attributes."""
    unique_loaded_items = []
    for name, alias in items.items():
        if isinstance(alias, bool):
            alias = name
        try:
            item = getattr(module, name)
            unique_loaded_items.append(item)
            if alias and alias != name:
                setattr(module, alias, item)
        except AttributeError as e:
            print(f"Attribute {name} not found in module {module.__name__}")
            if hasattr(module, "__path__"):
                try:
                    item = importlib.import_module(f"{module.__name__}.{name}")
                    sys.modules[f"{module.__name__}.{name}"] = item
                    unique_loaded_items.append(item)
                    if alias and alias != name:
                        setattr(module, alias, item)
                    print(f"Imported {name} from submodule and set alias {alias}.")
                except ImportError as ie:
                    print(f"Failed to import {name} from {module.__name__}: {str(ie)}")
                    continue
            else:
                print(
                    f"{name} is expected to be a direct attribute of {module.__name__}, not a submodule."
                )

    return unique_loaded_items


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
) -> Optional[tuple[types.ModuleType, ...]]:
    """Core Import Process."""
    target_path = path.join(*(target.split(".")))
    dir_path, file_name = path.split(target_path)
    caller_dir = get_caller_dir(target, base_path, dir_path)
    full_target = path.normpath(path.join(caller_dir, target_path))
    full_target = smart_join(caller_dir, target_path)

    # Check if the target is a directory
    if path.isdir(full_target):
        module_name = override_name if override_name else path.basename(full_target)
        module = create_jac_py_module(mod_bundle, module_name, dir_path, full_target)

        init_file = path.join(full_target, "__init__")
        if path.exists(init_file + ".py"):
            exec_init_file(init_file + ".py", module, caller_dir)
        elif path.exists(init_file + ".jac"):
            exec_init_file(init_file + ".jac", module, caller_dir)
        # load_submodules(module, full_target, cachable, mod_bundle)
    else:
        if lng == "jac":
            full_target += ".jac"
        else:
            full_target += ".py"

        module_name = path.splitext(file_name)[0]
        package_path = dir_path.replace(path.sep, ".")

        if package_path and f"{package_path}.{module_name}" in sys.modules:
            module = sys.modules[f"{package_path}.{module_name}"]
        elif not package_path and module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            if lng == "py":
                module, *loaded_items = py_import(
                    target=target,
                    caller_dir=caller_dir,
                    items=items,
                    absorb=absorb,
                    mdl_alias=mdl_alias,
                )
            else:
                module_name = override_name if override_name else module_name
                module = create_jac_py_module(
                    mod_bundle,
                    module_name,
                    package_path,
                    full_target,
                    push_to_sys="." not in target,
                )
                if mod_bundle:
                    codeobj = mod_bundle.mod_deps[full_target].gen.py_bytecode
                    codeobj = (
                        marshal.loads(codeobj) if isinstance(codeobj, bytes) else None
                    )
                else:
                    gen_dir = path.join(caller_dir, Con.JAC_GEN_DIR)
                    pyc_file_path = path.join(gen_dir, module_name + ".jbc")
                    if cachable and path.exists(pyc_file_path):
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
                with sys_path_context(caller_dir):
                    module.__file__ = full_target
                    exec(codeobj, module.__dict__)
        if "." in target:
            parent_module_name, submodule_name = target.rsplit(".", 1)
            parent_module = ensure_parent_module(parent_module_name, full_target)
            setattr(parent_module, submodule_name, module)
            if items:
                return process_items(module, items, target)
            return (parent_module,)

    unique_loaded_items = []
    if items:
        unique_loaded_items = process_items(module, items, target)
    return (
        (module,)
        if absorb or (not items or not len(items))
        else (*unique_loaded_items,)
    )


def exec_init_file(init_file: str, module: types.ModuleType, caller_dir: str) -> None:
    """Execute __init__.py or __init__.jac file to initialize the package."""
    if init_file.endswith(".py"):
        spec = importlib.util.spec_from_file_location(module.__name__, init_file)
        if spec is None:
            raise ImportError(f"Cannot create spec for {init_file}")
        init_module = importlib.util.module_from_spec(spec)
        sys.modules[module.__name__] = init_module
        if spec.loader is None:
            raise ImportError(f"Cannot load module from spec for {init_file}")
        spec.loader.exec_module(init_module)
    elif init_file.endswith(".jac"):
        result = compile_jac(init_file, cache_result=True)
        if result.errors_had or not result.ir.gen.py_bytecode:
            for e in result.errors_had:
                print(e)
                logging.error(e)
            return None
        codeobj = marshal.loads(result.ir.gen.py_bytecode)
        with sys_path_context(caller_dir):
            exec(codeobj, module.__dict__)


def load_submodules(
    parent_module: types.ModuleType,
    package_path: str,
    cachable: bool,
    mod_bundle: Optional[Module],
) -> None:
    """Recursively load submodules of a package."""
    for root, _, files in os.walk(package_path):
        for file in files:
            if file.endswith(".jac") or file.endswith(".py"):
                submodule_name = path.splitext(file)[0]
                full_submodule_name = f"{parent_module.__name__}.{submodule_name}"
                full_submodule_path = path.join(root, file)

                if file.endswith(".jac"):
                    result = compile_jac(full_submodule_path, cache_result=cachable)
                    if result.errors_had or not result.ir.gen.py_bytecode:
                        for e in result.errors_had:
                            print(f"Error compiling {full_submodule_path}: {e}")
                            logging.error(e)
                        continue

                    codeobj = marshal.loads(result.ir.gen.py_bytecode)
                    if not codeobj:
                        raise ImportError(
                            f"No bytecode found for {full_submodule_path}"
                        )
                else:
                    spec = importlib.util.spec_from_file_location(
                        full_submodule_name, full_submodule_path
                    )
                    if spec is None:
                        raise ImportError(
                            f"Cannot create spec for {full_submodule_name}"
                        )
                    submodule = importlib.util.module_from_spec(spec)
                    sys.modules[full_submodule_name] = submodule
                    if spec.loader is None:
                        raise ImportError(
                            f"Cannot load module from spec for {full_submodule_name}"
                        )
                    spec.loader.exec_module(submodule)
                    setattr(parent_module, submodule_name, submodule)
                    continue

                spec = importlib.util.spec_from_loader(full_submodule_name, loader=None)
                if spec is None:
                    raise ImportError(f"Cannot create spec for {full_submodule_name}")
                submodule = importlib.util.module_from_spec(spec)
                submodule.__file__ = full_submodule_path
                sys.modules[full_submodule_name] = submodule
                exec(codeobj, submodule.__dict__)

                setattr(parent_module, submodule_name, submodule)


def ensure_parent_module(module_name: str, full_target: str) -> types.ModuleType:
    """Ensure that the module is created and added to sys.modules, set as a package if its directory is a package."""
    try:
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            module = types.ModuleType(module_name)
            sys.modules[module_name] = module
        module_directory = path.dirname(full_target)
        if path.isdir(module_directory):
            module.__path__ = [module_directory]
        parent_name, _, child_name = module_name.rpartition(".")
        if parent_name:
            parent_module = ensure_parent_module(parent_name, module_directory)
            setattr(parent_module, child_name, module)
        return module
    except Exception as e:
        raise ImportError(f"Error creating module {module_name}: {e}") from e


def create_jac_py_module(
    mod_bundle: Optional[Module],
    module_name: str,
    package_path: str,
    full_target: str,
    push_to_sys: bool = True,
) -> types.ModuleType:
    """Create a module and ensure all parent namespaces are registered in sys.modules."""
    full_module_name = f"{package_path}.{module_name}" if package_path else module_name

    # Initialize the module and set its attributes
    module = types.ModuleType(full_module_name)
    module.__file__ = full_target
    module.__name__ = full_module_name
    module.__dict__["__jac_mod_bundle__"] = mod_bundle

    # Build and register the module's full namespace in sys.modules
    namespace_parts = full_module_name.split(".")
    constructed_path = ""
    for i, part in enumerate(namespace_parts):
        if i != 0:
            constructed_path += "."
        constructed_path += part

        # Ensure each part of the namespace exists in sys.modules
        if constructed_path not in sys.modules:
            interim_module = types.ModuleType(constructed_path)
            interim_module.__package__ = ".".join(constructed_path.split(".")[:-1])
            if (
                i == len(namespace_parts) - 1
            ):  # Only the last part gets the __file__ and __path__
                interim_module.__file__ = full_target
            if os.path.isdir(os.path.dirname(full_target)):
                interim_module.__path__ = [os.path.dirname(full_target)]
            sys.modules[constructed_path] = interim_module

        # Set parent-child relationship
        if i > 0:
            parent_path = ".".join(namespace_parts[:i])
            parent_module = sys.modules[parent_path]
            setattr(parent_module, part, sys.modules[constructed_path])

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
    items: Optional[dict[str, Union[str, bool]]] = None,
    absorb: bool = False,
    mdl_alias: Optional[str] = None,
) -> tuple[types.ModuleType, ...]:
    """Import a Python module."""
    try:
        loaded_items: list = []

        if target.startswith("."):
            target = target.lstrip(".")
            full_target = path.normpath(path.join(caller_dir, target))
            spec = importlib.util.spec_from_file_location(target, full_target + ".py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
            else:
                raise ImportError(f"Cannot find module {target} at {full_target}")
        else:
            module = importlib.import_module(name=target)

        main_module = __import__("__main__")

        if absorb:
            for name in dir(module):
                if not name.startswith("_"):
                    setattr(main_module, name, getattr(module, name))

        elif items:
            for name, alias in items.items():
                if isinstance(alias, bool):
                    alias = name
                try:
                    item = getattr(module, name)
                    if item not in loaded_items:
                        setattr(
                            main_module, alias if isinstance(alias, str) else name, item
                        )
                        loaded_items.append(item)
                except AttributeError as e:
                    if hasattr(module, "__path__"):
                        item = importlib.import_module(f"{target}.{name}")
                        if item not in loaded_items:
                            setattr(
                                main_module,
                                alias if isinstance(alias, str) else name,
                                item,
                            )
                            loaded_items.append(item)
                    else:
                        raise e

        else:
            setattr(
                __import__("__main__"),
                mdl_alias if isinstance(mdl_alias, str) else target,
                module,
            )

        return (module, *loaded_items)

    except ImportError as e:
        raise e
