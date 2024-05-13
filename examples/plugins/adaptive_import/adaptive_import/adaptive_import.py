from jaclang.plugin.default import hookimpl
import ray
import asyncio
import sys
from .library_monitor import LibraryMonitor
from .policy_manager import PolicyManager
from .module_loader import ModuleLoader
import types
from typing import Any, Callable, Optional, Type, TypeAlias, Union
from jaclang.compiler.absyntree import Module
import pluggy
from jaclang.plugin.spec import JacBuiltin, JacCmdSpec, JacFeatureSpec
import logging
import marshal
from os import getcwd, path
from jaclang.compiler.constant import Constants as Con
from jaclang.compiler.compile import compile_jac
import importlib

pm = pluggy.PluginManager("jac")
pm.add_hookspecs(JacFeatureSpec)
pm.add_hookspecs(JacCmdSpec)
pm.add_hookspecs(JacBuiltin)


logging.basicConfig(level=logging.DEBUG)  # Set logging to debug level
logger = logging.getLogger(__name__)

pm = pluggy.PluginManager("jac")
pm.add_hookspecs(JacFeatureSpec)
pm.add_hookspecs(JacCmdSpec)
pm.add_hookspecs(JacBuiltin)


def load_module_remotely(target, remote_address):
    """Load a module using Ray in a remote setting."""
    if not ray.is_initialized():
        ray.init(address=remote_address)

    async def async_load_module():
        library_monitor = LibraryMonitor()
        policy_manager = PolicyManager(library_monitor)
        module_loader = ModuleLoader(policy_manager, use_ray_object_store=True)
        return await module_loader.load_module(target)

    loop = asyncio.get_event_loop()
    module = loop.run_until_complete(async_load_module())
    if module:
        sys.modules[module.__name__] = module


def jac_importer(
    target: str,
    base_path: str,
    absorb: bool = False,
    cachable: bool = True,
    mdl_alias: Optional[str] = None,
    override_name: Optional[str] = None,
    mod_bundle: Optional[Module] = None,
    lng: Optional[str] = None,
    items: Optional[dict[str, Union[str, bool]]] = None,
) -> Optional[types.ModuleType]:
    """Core Import Process."""

    print(f"jac_importer: lang: {lng}")
    dir_path, file_name = (
        path.split(path.join(*(target.split("."))) + ".py")
        if lng == "py"
        else path.split(path.join(*(target.split("."))) + ".jac")
    )
    module_name = path.splitext(file_name)[0]
    package_path = dir_path.replace(path.sep, ".")

    if package_path and f"{package_path}.{module_name}" in sys.modules and lng != "py":
        return sys.modules[f"{package_path}.{module_name}"]
    elif not package_path and module_name in sys.modules and lng != "py":
        return sys.modules[module_name]

    caller_dir = path.dirname(base_path) if not path.isdir(base_path) else base_path
    if not caller_dir:
        caller_dir = getcwd()
    chomp_target = target
    if chomp_target.startswith("."):
        chomp_target = chomp_target[1:]
        while chomp_target.startswith("."):
            caller_dir = path.dirname(caller_dir)
            chomp_target = chomp_target[1:]
    caller_dir = path.join(caller_dir, dir_path)

    full_target = path.normpath(path.join(caller_dir, file_name))
    path_added = False
    if caller_dir not in sys.path:
        sys.path.append(caller_dir)
        path_added = True

    module_name = override_name if override_name else module_name
    module = types.ModuleType(module_name)
    module.__file__ = full_target
    module.__name__ = module_name
    module.__dict__["__jac_mod_bundle__"] = mod_bundle
    if lng != "py":
        if mod_bundle:
            codeobj = (
                mod_bundle.gen.py_bytecode
                if full_target == mod_bundle.loc.mod_path
                else mod_bundle.mod_deps[full_target].gen.py_bytecode
            )
            if isinstance(codeobj, bytes):
                codeobj = marshal.loads(codeobj)
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

        if package_path:
            parts = package_path.split(".")
            for i in range(len(parts)):
                package_name = ".".join(parts[: i + 1])
                if package_name not in sys.modules:
                    sys.modules[package_name] = types.ModuleType(package_name)

            setattr(sys.modules[package_path], module_name, module)
            sys.modules[f"{package_path}.{module_name}"] = module
        sys.modules[module_name] = module

        if not codeobj:
            raise ImportError(f"No bytecode found for {full_target}")
        exec(codeobj, module.__dict__)

    (
        py_import(target=target, items=items, absorb=absorb, mdl_alias=mdl_alias)
        if lng == "py" or lng == "jac"
        else None
    )

    if path_added:
        sys.path.remove(caller_dir)

    return module


def py_import(
    target: str,
    items: Optional[dict[str, Union[str, bool]]] = None,
    absorb: bool = False,
    mdl_alias: Optional[str] = None,
    use_remote: bool = False,
    module_loader: Optional[ModuleLoader] = None,
) -> None:
    """Import a Python module, optionally using the ModuleLoader for remote modules."""
    try:
        print(f"Importing module {target}")
        if use_remote and module_loader:
            imported_module = module_loader.load_module(target)
        else:
            target = target.lstrip(".") if target.startswith("..") else target
            imported_module = importlib.import_module(target)

        main_module = __import__("__main__")

        if absorb:
            for name in dir(imported_module):
                if not name.startswith("_"):
                    setattr(main_module, name, getattr(imported_module, name))

        elif items:
            for name, alias in items.items():
                setattr(
                    main_module,
                    alias if isinstance(alias, str) else name,
                    getattr(imported_module, name),
                )

        else:
            setattr(
                main_module,
                mdl_alias if isinstance(mdl_alias, str) else target,
                imported_module,
            )

    except ImportError:
        print(f"Failed to import module {target}")


# def py_import(
#     target: str,
#     items: Optional[dict[str, Union[str, bool]]] = None,
#     absorb: bool = False,
#     mdl_alias: Optional[str] = None,
# ) -> None:
#     """Import a Python module."""
#     try:
#         target = target.lstrip(".") if target.startswith("..") else target
#         imported_module = importlib.import_module(target)
#         main_module = __import__("__main__")
#         # importer = importlib.import_module(caller)
#         if absorb:
#             for name in dir(imported_module):
#                 if not name.startswith("_"):
#                     setattr(main_module, name, getattr(imported_module, name))

#         elif items:
#             for name, alias in items.items():
#                 setattr(
#                     main_module,
#                     alias if isinstance(alias, str) else name,
#                     getattr(imported_module, name),
#                 )

#         else:
#             setattr(
#                 __import__("__main__"),
#                 mdl_alias if isinstance(mdl_alias, str) else target,
#                 imported_module,
#             )
#     except ImportError:
#         print(f"Failed to import module {target}")


class JacFeature:
    @staticmethod
    @hookimpl
    def jac_import(
        target: str,
        base_path: str,
        absorb: bool = False,
        cachable: bool = True,
        mdl_alias: Optional[str] = None,
        override_name: Optional[str] = None,
        mod_bundle: Optional[Module] = None,
        lng: Optional[str] = None,
        items: Optional[dict[str, Union[str, bool]]] = None,
        use_remote: bool = False,
        remote_address: str = "",  #  "ray://localhost:10001",
    ) -> Optional[types.ModuleType]:
        logger.debug(
            f"Attempting to load module '{target}' with remote set to {use_remote}."
        )
        if use_remote:
            module = jac_importer(
                target=target,
                base_path=base_path,
                absorb=absorb,
                cachable=cachable,
                mdl_alias=mdl_alias,
                override_name=override_name,
                mod_bundle=mod_bundle,
                lng=lng,
                items=items,
                # remote=use_remote,
                # remote_address=remote_address,
            )

            if module:
                logger.info(
                    f"Module '{target}' successfully loaded {'remotely' if use_remote else 'locally'}."
                )
            else:
                logger.error(
                    f"Failed to load module '{target}' {'remotely' if use_remote else 'locally'}."
                )
            return module
        else:
            try:
                module = pm.hook.jac_import(
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
                print(f"lang in adaptive: {lng}")
                if module:
                    logger.info(f"Module '{target}' successfully loaded locally.")
                else:
                    logger.warning(
                        f"No module was returned from local loading for '{target}'."
                    )
                    logger.warning(
                        f"Module '{module}' returned from remote loading for '{target}'."
                    )
                return module
            except Exception as e:
                logger.error(f"Error while loading module '{target}' locally: {e}")
                return None
