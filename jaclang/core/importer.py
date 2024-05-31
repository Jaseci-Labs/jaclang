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


def compile_and_load_jac_modules(
    package_name: str,
    package_path: str,
    cachable: bool,
    mod_bundle: Optional[Module] = None,
) -> list:
    """Compile and prepare the Jac package, and load submodules."""
    submodules: list[types.ModuleType] = []
    for root, _, files in os.walk(package_path):
        for file in files:
            if file.endswith(".jac"):
                submodule_name = path.splitext(file)[0]
                full_submodule_name = f"{package_name}.{submodule_name}"
                full_submodule_path = path.join(root, file)

                # Compile the submodule
                result = compile_jac(full_submodule_path, cache_result=cachable)
                if result.errors_had or not result.ir.gen.py_bytecode:
                    for e in result.errors_had:
                        print(f"Error compiling {full_submodule_path}: {e}")
                        logging.error(e)
                    continue

                codeobj = marshal.loads(result.ir.gen.py_bytecode)
                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_submodule_path}")

                # Create and load the submodule
                spec = importlib.util.spec_from_loader(full_submodule_name, loader=None)
                submodule = importlib.util.module_from_spec(spec) if spec else None
                if not submodule:
                    raise ImportError(
                        f"Failed to create module for {full_submodule_name}"
                    )
                submodule.__file__ = full_submodule_path  # Define __file__ attribute
                # submodule.__jac_mod_bundle__ = mod_bundle  # Set __jac_mod_bundle__
                sys.modules[full_submodule_name] = submodule
                # exec(codeobj, submodule.__dict__)

                # # Add submodule to parent package
                # parent_module = sys.modules[package_name]
                # setattr(parent_module, submodule_name, submodule)

                # Print debug information about the submodule
                print(f"Loaded submodule: {full_submodule_name}")
                print(f"Attributes of {full_submodule_name}: {dir(submodule)}")

                submodules.append(submodule)
    return submodules


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
    loaded_items: list = []

    # Determine if the target is a directory or file
    target_path = path.join(*(target.split(".")))
    dir_path, file_name = path.split(target_path)
    caller_dir = get_caller_dir(target, base_path, dir_path)
    full_target = path.normpath(path.join(caller_dir, target_path))

    if path.isdir(full_target):
        # It's a directory, handle directory import
        module_name = override_name if override_name else path.basename(full_target)
        module = create_jac_py_module(mod_bundle, module_name, dir_path, full_target)
        submodules = compile_and_load_jac_modules(module_name, full_target, cachable)
        loaded_items.extend(submodules)
    else:
        # It's a file, handle file import
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
                    mod_bundle, module_name, package_path, full_target
                )
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
                            return None
                        else:
                            codeobj = marshal.loads(result.ir.gen.py_bytecode)
                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_target}")
                with sys_path_context(caller_dir):
                    module.__file__ = full_target
                    exec(codeobj, module.__dict__)

    unique_loaded_items = []
    if items:
        for name, _ in items.items():
            try:
                item = getattr(module, name)
                if item not in unique_loaded_items:
                    unique_loaded_items.append(item)
            except AttributeError as e:
                if hasattr(module, "__path__"):
                    item = importlib.import_module(f"{target}.{name}")
                    if item not in unique_loaded_items:
                        unique_loaded_items.append(item)
                else:
                    raise e

    return (
        (module,)
        if absorb or (not items or not len(items))
        else (*unique_loaded_items,)
    )


def create_jac_py_module(
    mod_bundle: Optional[Module], module_name: str, package_path: str, full_target: str
) -> types.ModuleType:
    """Create a module."""
    module = types.ModuleType(module_name)
    module.__file__ = full_target
    module.__name__ = module_name
    module.__dict__["__jac_mod_bundle__"] = mod_bundle
    if package_path:
        parts = package_path.split(".")
        for i in range(len(parts)):
            package_name = ".".join(parts[: i + 1])
            if package_name not in sys.modules:
                sys.modules[package_name] = types.ModuleType(package_name)

        setattr(sys.modules[package_path], module_name, module)
        sys.modules[f"{package_path}.{module_name}"] = module
    sys.modules[module_name] = module
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
            # print(f"Debug: Full target for relative import: {full_target}")
            spec = importlib.util.spec_from_file_location(target, full_target + ".py")
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                # print(f"Debug: Successfully imported relative module: {module}")
            else:
                raise ImportError(f"Cannot find module {target} at {full_target}")
        else:
            # print(f"Importing module: {target}")
            module = importlib.import_module(name=target)

        main_module = __import__("__main__")

        if absorb:
            for name in dir(module):
                if not name.startswith("_"):
                    setattr(main_module, name, getattr(module, name))

        elif items:
            for name, alias in items.items():
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
        print(f"Failed to import module {target}: {e}")
        raise e
