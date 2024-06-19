"""Special Imports for Jac Code."""

import hashlib
import importlib
import marshal
import os
import sys
import types
from os import getcwd, path
from typing import Optional, Union, Tuple

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context
from jaclang.utils.log import logging


base_mod_path: str = ""


def get_full_target(target: str, base_path: str) -> str:
    global caller_dir, dir_path, file_name, base_mod_path
    target_path = path.join(*(target.split(".")))
    dir_path, file_name = path.split(target_path)
    caller_dir = get_caller_dir(target, base_path, dir_path)
    full_target = path.normpath(path.join(caller_dir, target_path))
    full_target = smart_join(caller_dir, target_path)
    if not base_mod_path:
        if not os.path.isdir(base_path):
            base_mod_path = os.path.dirname(base_path)
        else:
            base_mod_path = base_path
    base_mod_path = base_mod_path
    # print(f"base_mod_path: {base_mod_path}")
    return full_target


def resolve_sys_mod_name(target: str, full_path: str) -> str:
    """Resolve system module name from the given full path of a file and the base module path."""
    global base_mod_path
    full_path = os.path.abspath(full_path)
    if not full_path.startswith(base_mod_path):
        return
    # base_mod_path = os.path.abspath(base_mod_path)
    rel_path = os.path.relpath(full_path, base_mod_path)
    if rel_path.endswith(".jac"):
        rel_path = rel_path[:-4]
    mod_name = rel_path.replace(os.sep, ".").strip(".")
    if mod_name.endswith(".__init__"):
        mod_name = mod_name[:-9]  # Remove the '.__init__' suffix
    # print(
    #     f"Resolving system module name: {mod_name}, full_path: {full_path}, basepath: {base_mod_path} ,rel_name: {rel_path}, target_path: {target}"
    # )
    # print(f"return: {mod_name}")
    return mod_name


def smart_join(base_path: str, target_path: str) -> str:
    """Join two paths while attempting to remove any redundant segments."""
    base_parts = path.normpath(base_path).split(path.sep)
    target_parts = path.normpath(target_path).split(path.sep)

    # Attempt to detect and remove overlapping segments
    while base_parts and target_parts and base_parts[-1] == target_parts[0]:
        target_parts.pop(0)

    full_path = path.join(base_path, *target_parts)
    return path.normpath(full_path)


def process_items(module, items, lng, caller_dir, cachable, mod_bundle):
    """Extracts items from a module, renaming them if specified, and handles missing attributes."""
    unique_loaded_items = []
    module_dir = (
        module.__path__[0]
        if hasattr(module, "__path__")
        else os.path.dirname(getattr(module, "__file__", ""))
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
                item = load_jac_file(module, name, jac_file_path, mod_bundle, cachable)
                if item:
                    setattr(module, name, item)
                    unique_loaded_items.append(item)
                    if alias and alias != name:
                        setattr(module, alias, item)
            elif lng == "py":
                if hasattr(module, "__path__"):
                    item = importlib.import_module(f"{module.__name__}.{name}")
                    if item not in unique_loaded_items:
                        unique_loaded_items.append(item)
            else:
                # Attempt to load the item from the module's file directly
                jac_file_path = module.__file__
                if os.path.isfile(jac_file_path):
                    item = load_jac_file(
                        module, name, jac_file_path, mod_bundle, cachable
                    )
                    if item:
                        setattr(module, name, item)
                        unique_loaded_items.append(item)
                        if alias and alias != name:
                            setattr(module, alias, item)

    return unique_loaded_items


def load_jac_file(module, name, jac_file_path, mod_bundle, cachable):
    global full_target
    try:
        # print(f"Loading {name} from {jac_file_path} in {module.__name__} package.")
        package_name = (
            f"{module.__name__}.{name}"
            if hasattr(module, "__path__")
            else module.__name__
        )
        if package_name not in sys.modules:
            full_target = jac_file_path
            # print(f"Handing load_jac_file: {full_target}")
            new_module = create_jac_py_module(
                mod_bundle, name, module.__name__, full_target
            )
        else:
            new_module = sys.modules[package_name]

        codeobj = get_codeobj(full_target, name, mod_bundle, cachable)
        if not codeobj:
            raise ImportError(f"No bytecode found for {full_target}")

        exec(codeobj, new_module.__dict__)
        return getattr(new_module, name, new_module)
    except ImportError as e:
        print(
            f"Failed to load {name} from {jac_file_path} in {module.__name__}: {str(e)}"
        )
        return None


def get_codeobj(
    full_target: str,
    module_name: str,
    mod_bundle: Optional[types.ModuleType],
    cachable: bool,
) -> types.CodeType:
    if mod_bundle:
        codeobj = mod_bundle.mod_deps[full_target].gen.py_bytecode
        return marshal.loads(codeobj) if isinstance(codeobj, bytes) else None

    gen_dir = os.path.join(caller_dir, Con.JAC_GEN_DIR)
    pyc_file_path = os.path.join(gen_dir, module_name + ".jbc")
    if cachable and os.path.exists(pyc_file_path):
        with open(pyc_file_path, "rb") as f:
            return marshal.load(f)

    result = compile_jac(full_target, cache_result=cachable)
    if result.errors_had or not result.ir.gen.py_bytecode:
        for e in result.errors_had:
            print(e)
            logging.error(e)
        return None
    return marshal.loads(result.ir.gen.py_bytecode)


def handle_directory(
    full_target: str,
    override_name: Optional[str],
    mod_bundle: Optional[types.ModuleType],
    # dir_path: str,
) -> types.ModuleType:
    module_name = path.splitext(file_name)[0]
    module_name = override_name if override_name else module_name
    package_path = dir_path.replace(path.sep, ".")
    # print(
    #     f"module_name: {module_name}, package_path: {package_path}, dir_path: {dir_path}"
    # )
    module = create_jac_py_module(mod_bundle, module_name, package_path, full_target)
    init_file = os.path.join(full_target, "__init__")
    if os.path.exists(init_file + ".py"):
        exec_init_file(init_file + ".py", module, caller_dir)
    elif os.path.exists(init_file + ".jac"):
        exec_init_file(init_file + ".jac", module, caller_dir)
    # print(f"module: {module}, module_dicle: {module.__dict__}")
    return module


# def get_full_target(target: str, base_path: str) -> str:
#     global caller_dir, dir_path, file_name, base_mod_path
#     target_path = path.join(*(target.split(".")))
#     dir_path, file_name = path.split(target_path)
#     caller_dir = get_caller_dir(target, base_path, dir_path)
#     full_target = path.normpath(path.join(caller_dir, target_path))
#     full_target = smart_join(caller_dir, target_path)
#     if not base_mod_path:
#         if not os.path.isdir(base_path):
#             base_mod_path = os.path.dirname(base_path)
#         else:
#             base_mod_path = base_path
#     base_mod_path = base_mod_path
#     # print(f"base_mod_path: {base_mod_path}")
#     return full_target


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
) -> Optional[Tuple[types.ModuleType, ...]]:
    """Core Import Process."""
    # global caller_dir, dir_path, file_name, base_mod_path
    # print(f"resolving: {target} in {base_path} relpath {resolve_sys_mod_name(target)})")
    full_target = get_full_target(target, base_path)

    # Handle directory import
    if os.path.isdir(full_target):
        module = handle_directory(full_target, override_name, mod_bundle)
    else:
        full_target += ".jac" if lng == "jac" else ".py"
        if lng == "py":
            module_name = path.splitext(file_name)[0]
        else:
            module_name = resolve_sys_mod_name(target, full_target)
        package_path = dir_path.replace(path.sep, ".")

        module = sys.modules.get(
            f"{package_path}.{module_name}" if package_path else module_name
        )
        if not module:
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
                codeobj = get_codeobj(full_target, module_name, mod_bundle, cachable)
                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_target}")
                with sys_path_context(caller_dir):
                    module.__file__ = full_target
                    exec(codeobj, module.__dict__)

        if "." in target:
            parent_module_name, submodule_name = target.rsplit(".", 1)
            parent_module = ensure_parent_module(
                parent_module_name, full_target, mod_bundle
            )
            # print(f"parent_module: {parent_module}, module: {module}, items: {items}")
            setattr(parent_module, submodule_name, module)
            if items:
                return process_items(
                    module, items, lng, caller_dir, cachable, mod_bundle
                )
            # print(f"module: {module}, module_dicle: {module.__dict__.keys()}")
            return (parent_module,) if not mdl_alias else (module,)
    unique_loaded_items = (
        process_items(module, items, lng, caller_dir, cachable, mod_bundle)
        if items
        else []
    )
    return (module,) if absorb or not items else tuple(unique_loaded_items)


def exec_init_file(init_file: str, module: types.ModuleType, caller_dir: str) -> None:
    """Execute __init__.py or __init__.jac file to initialize the package."""
    if init_file.endswith(".py"):
        spec = importlib.util.spec_from_file_location(module.__name__, init_file)
        if spec is None:
            raise ImportError(f"Cannot create spec for {init_file}")
        init_module = importlib.util.module_from_spec(spec)
        # print(f"adding module {module.__name__} to sys.modules")
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


def ensure_parent_module(
    module_name: str, full_target: str, mod_bundle: Module
) -> types.ModuleType:
    """Ensure that the module is created and added to sys.modules, set as a package if its directory is a package."""
    try:
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # print(f"module_name in ensure: {module_name}")
            module = types.ModuleType(module_name)
            module.__dict__["__jac_mod_bundle__"] = mod_bundle

            if hasattr(module_name, "__name__"):
                sys.modules[module_name] = module
        module_directory = path.dirname(full_target)
        if path.isdir(module_directory):
            module.__path__ = [module_directory]
        parent_name, _, child_name = module_name.rpartition(".")
        if parent_name:
            parent_module = ensure_parent_module(
                parent_name, module_directory, mod_bundle
            )
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
    module = sys.modules.get(
        f"{package_path}.{module_name}" if package_path else module_name
    )
    if not module:
        module_name = resolve_sys_mod_name(module_name, full_target)
        module = types.ModuleType(module_name)
        module.__name__ = module_name
    module.__dict__["__jac_mod_bundle__"] = mod_bundle

    if os.path.isdir(full_target):
        # print(f"module_name: {module}, full_target: {full_target} is directory")
        module.__path__ = [full_target]
        init_file = os.path.join(full_target, "__init__.jac")
        if os.path.isfile(init_file):
            module.__file__ = init_file
    else:
        module.__file__ = full_target

    namespace_parts = module_name.split(".")
    constructed_path = ""

    for i, part in enumerate(namespace_parts):
        constructed_path = f"{constructed_path}.{part}" if constructed_path else part
        if constructed_path not in sys.modules:
            interim_module = types.ModuleType(constructed_path)
            interim_module.__package__ = ".".join(constructed_path.split(".")[:-1])
            interim_module.__dict__["__jac_mod_bundle__"] = mod_bundle
            if os.path.isdir(os.path.dirname(full_target)):
                interim_module.__path__ = [os.path.dirname(full_target)]
            if i == len(namespace_parts) - 1 and not os.path.isdir(
                full_target
            ):  # Set __file__ for the final component if it's a file
                # if hasattr(module, "__file__"):
                # print(f"interim_module: {interim_module}, module: {module}")
                interim_module.__file__ = module.__file__
            # print(f"create adding module {constructed_path} to sys.modules")
            sys.modules[constructed_path] = interim_module
        if i > 0:
            parent_path = ".".join(namespace_parts[:i])
            parent_module = sys.modules[parent_path]
            setattr(parent_module, part, sys.modules[constructed_path])
    # print(f"Returning from JAC, module_name: {module}, full_target: {full_target}")
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
                # print(f"adding module {spec.name} to sys.modules")
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
        # print(f"loaded_items: {loaded_items}, module: {module}")
        return (module, *loaded_items)

    except ImportError as e:
        raise e
