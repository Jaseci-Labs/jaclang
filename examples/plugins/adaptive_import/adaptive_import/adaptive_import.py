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
from jaclang.core.utils import sys_path_context


logging.basicConfig(level=logging.DEBUG)  # Set logging to debug level
logger = logging.getLogger(__name__)

pm = pluggy.PluginManager("jac")
pm.add_hookspecs(JacFeatureSpec)
pm.add_hookspecs(JacCmdSpec)
pm.add_hookspecs(JacBuiltin)


def load_module_remotely(target, remote_address: str = "auto"):
    """Load a module using Ray in a remote setting."""
    print(f"Loading module {target} remotely...")
    if not ray.is_initialized():
        ray.init(address=remote_address)

    async def async_load_module():
        library_monitor = LibraryMonitor()
        policy_manager = PolicyManager(library_monitor)
        module_loader = ModuleLoader(policy_manager, use_ray_object_store=True)
        return await module_loader.load_module(target)

    loop = asyncio.get_event_loop()
    module = loop.run_until_complete(async_load_module())
    # if module:
    #     sys.modules[module.__name__] = module
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
    use_remote: bool = False,
    use_ray_object_store: bool = False,
    remote_address: str = "auto",
) -> Optional[types.ModuleType]:
    """Core Import Process."""
    library_monitor = LibraryMonitor()
    policy_manager = PolicyManager(library_monitor)
    module_loader = ModuleLoader(policy_manager, use_ray_object_store)
    dir_path, file_name = path.split(
        path.join(*(target.split("."))) + (".jac" if lng == "jac" else ".py")
    )
    module_name = path.splitext(file_name)[0]
    package_path = dir_path.replace(path.sep, ".")

    if package_path and f"{package_path}.{module_name}" in sys.modules:
        return sys.modules[f"{package_path}.{module_name}"]
    elif not package_path and module_name in sys.modules:
        return sys.modules[module_name]

    caller_dir = get_caller_dir(target, base_path, dir_path)
    full_target = path.normpath(path.join(caller_dir, file_name))
    if lng == "py":
        module = py_import(
            target=target,
            items=items,
            absorb=absorb,
            mdl_alias=mdl_alias,
            use_remote=use_remote,
            module_loader=module_loader,
            remote_address=remote_address,
        )

    else:
        module_name = override_name if override_name else module_name
        module = create_jac_py_module(
            mod_bundle, module_name, package_path, full_target
        )
        if mod_bundle:
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
        print(f"Compiling module {full_target}, module dict is {module.__dict__}")
        with sys_path_context(caller_dir):
            exec(codeobj, module.__dict__)

    return module


def py_import(
    target: str,
    items: Optional[dict[str, Union[str, bool]]] = None,
    absorb: bool = False,
    mdl_alias: Optional[str] = None,
    use_remote: bool = True,
    module_loader: Optional[ModuleLoader] = None,
    remote_address: str = "auto",
) -> types.ModuleType:
    """Import a Python module, optionally using the ModuleLoader for remote modules."""
    try:
        # print(f"Importing module {target}")
        if use_remote and module_loader:
            # print(f"Loading module {target} remotely")
            imported_module = load_module_remotely(
                target=target, remote_address=remote_address
            )
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
            print(f"main_module module {main_module}")
            setattr(
                __import__("__main__"),
                mdl_alias if isinstance(mdl_alias, str) else target,
                imported_module,
            )
            print(f"main_module module {main_module.__dict__}")
        return imported_module
    except ImportError as e:
        print(f"Failed to import module {target}")
        raise e


class JacFeature:
    @staticmethod
    @hookimpl
    def jac_import(
        target: str,
        base_path: str,
        absorb: bool,
        cachable: bool,
        mdl_alias: Optional[str],
        override_name: Optional[str],
        mod_bundle: Optional[Module],
        lng: Optional[str],
        items: Optional[dict[str, Union[str, bool]]],
        use_remote: bool = True,
        remote_address: str = "ray://localhost:10001",
    ) -> Optional[types.ModuleType]:
        # logger.info(
        # f"Attempting to load module '{target}' with remote set to {use_remote}."
        # )
        # print(f"lang in adaptive: {lng}, target: {target}")
        if use_remote:
            return jac_importer(
                target=target,
                base_path=base_path,
                absorb=absorb,
                cachable=cachable,
                mdl_alias=mdl_alias,
                override_name=override_name,
                mod_bundle=mod_bundle,
                lng=lng,
                items=items,
                use_remote=use_remote,
                remote_address=remote_address,
            )
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
                return module
            except Exception as e:
                logger.error(f"Error while loading module '{target}' locally: {e}")
                return None
