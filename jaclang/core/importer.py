"""Special Imports for Jac Code."""

import importlib
import marshal
import os
import sys
import types
from os import getcwd, path
from traceback import TracebackException
from typing import Optional, Union

from jaclang.compiler.absyntree import Module
from jaclang.compiler.compile import compile_jac
from jaclang.compiler.constant import Constants as Con
from jaclang.core.utils import sys_path_context


def handle_directory(
    module_name: str, full_mod_path: str, mod_bundle: Module
) -> types.ModuleType:
    """Import from a directory that potentially contains multiple Jac modules."""
    module = types.ModuleType(module_name)
    module.__name__ = module_name
    module.__path__ = [full_mod_path]
    module.__dict__["__jac_mod_bundle__"] = mod_bundle
    if module not in sys.modules:
        sys.modules[module_name] = module
    return module


def process_items(
    module: types.ModuleType,
    items: dict[str, Union[str, bool]],
    caller_dir: str,
    mod_bundle: Optional[Module] = None,
    cachable: bool = True,
) -> None:
    """Process items within a module by handling renaming and potentially loading missing attributes."""
    module_dir = (
        module.__path__[0]
        if hasattr(module, "__path__")
        else os.path.dirname(getattr(module, "__file__", ""))
    )
    for name, alias in items.items():
        try:
            item = getattr(module, name)
            if alias and alias != name and not isinstance(alias, bool):
                setattr(module, alias, item)
        except AttributeError:
            jac_file_path = os.path.join(module_dir, f"{name}.jac")
            if hasattr(module, "__path__") and os.path.isfile(jac_file_path):
                item = load_jac_file(
                    module=module,
                    name=name,
                    jac_file_path=jac_file_path,
                    mod_bundle=mod_bundle,
                    cachable=cachable,
                    caller_dir=caller_dir,
                )
                if item:
                    setattr(module, name, item)
                    if alias and alias != name and not isinstance(alias, bool):
                        setattr(module, alias, item)


def load_jac_file(
    module: types.ModuleType,
    name: str,
    jac_file_path: str,
    mod_bundle: Optional[Module],
    cachable: bool,
    caller_dir: str,
) -> Optional[types.ModuleType]:
    """Load a single .jac file into the specified module component."""
    try:
        package_name = (
            f"{module.__name__}.{name}"
            if hasattr(module, "__path__")
            else module.__name__
        )
        new_module = sys.modules.get(
            package_name,
            create_jac_py_module(mod_bundle, name, module.__name__, jac_file_path),
        )

        codeobj = get_codeobj(
            full_target=jac_file_path,
            module_name=name,
            mod_bundle=mod_bundle,
            cachable=cachable,
            caller_dir=caller_dir,
        )
        if not codeobj:
            raise ImportError(f"No bytecode found for {jac_file_path}")

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
    mod_bundle: Optional[Module],
    cachable: bool,
    caller_dir: str,
) -> Optional[types.CodeType]:
    """Execcutes the code for a given module."""
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
            return None
    if result.ir.gen.py_bytecode is not None:
        return marshal.loads(result.ir.gen.py_bytecode)
    else:
        return None


def jac_importer(
    target: str,
    base_path: str,
    absorb: bool = False,
    cachable: bool = True,
    mdl_alias: Optional[str] = None,
    override_name: Optional[str] = None,
    mod_bundle: Optional[Module | str] = None,
    lng: Optional[str] = "jac",
    items: Optional[dict[str, Union[str, bool]]] = None,
) -> Optional[types.ModuleType]:
    """Core Import Process."""
    dir_path, file_name = path.split(
        path.join(*(target.split("."))) + (".jac" if lng == "jac" else ".py")
    )
    module_name = path.splitext(file_name)[0]
    package_path = dir_path.replace(path.sep, ".")

    if (
        not override_name
        and package_path
        and f"{package_path}.{module_name}" in sys.modules
    ):
        return sys.modules[f"{package_path}.{module_name}"]
    elif not override_name and not package_path and module_name in sys.modules:
        return sys.modules[module_name]

    valid_mod_bundle = (
        sys.modules[mod_bundle].__jac_mod_bundle__
        if isinstance(mod_bundle, str)
        and mod_bundle in sys.modules
        and "__jac_mod_bundle__" in sys.modules[mod_bundle].__dict__
        else None
    )

    caller_dir = get_caller_dir(target, base_path, dir_path)
    full_target = path.normpath(path.join(caller_dir, file_name))

    if lng == "py":
        module = py_import(
            target=target,
            items=items,
            absorb=absorb,
            mdl_alias=mdl_alias,
            caller_dir=caller_dir,
        )
    else:
        module_name = override_name if override_name else module_name

        if os.path.isdir(path.splitext(full_target)[0]):
            module = handle_directory(
                module_name, path.splitext(full_target)[0], valid_mod_bundle
            )
            if items:
                process_items(
                    module,
                    items,
                    caller_dir,
                    mod_bundle=valid_mod_bundle,
                    cachable=cachable,
                )
        else:
            module = create_jac_py_module(
                valid_mod_bundle, module_name, package_path, full_target
            )
            codeobj = get_codeobj(
                full_target=full_target,
                module_name=module_name,
                mod_bundle=valid_mod_bundle,
                cachable=cachable,
                caller_dir=caller_dir,
            )
            try:
                if not codeobj:
                    raise ImportError(f"No bytecode found for {full_target}")
                with sys_path_context(caller_dir):
                    exec(codeobj, module.__dict__)

            except Exception as e:

                # TODO:
                #  - Move the stack trace dump to a different function.
                #  - `import:py blah;` This will contain
                #       1. stackframe of jac runtime -- remove them.
                #       2. py_import() prints "Failed to import module blah" -- should be a verbose debug message.
                trace_dump = ""

                # Utility function to get the error line char offset.
                def byte_offset_to_char_offset(string: str, offset: int) -> int:
                    return len(
                        string.encode("utf-8")[:offset].decode(
                            "utf-8", errors="replace"
                        )
                    )

                tb = TracebackException(
                    type(e), e, e.__traceback__, limit=None, compact=True
                )
                trace_dump += f"Error: {str(e)}"

                # The first frame is the call the to the above `exec` function, not usefull to the enduser,
                # and Make the most recent call first.
                tb.stack.pop(0)
                tb.stack.reverse()

                # FIXME: should be some settings, we should replace to ensure the anchors length match.
                dump_tab_width = 4

                for idx, frame in enumerate(tb.stack):
                    func_signature = frame.name + (
                        "()" if frame.name.isidentifier() else ""
                    )

                    # Pretty print the most recent call's location.
                    if idx == 0 and (frame.line and frame.line.strip() != ""):
                        line_o = frame._original_line.rstrip()  # type: ignore [attr-defined]
                        line_s = frame.line.rstrip() if frame.line else ""
                        stripped_chars = len(line_o) - len(line_s)
                        trace_dump += f'\n{" " * (dump_tab_width * 2)}{line_s}'
                        if frame.colno is not None and frame.end_colno is not None:
                            off_start = byte_offset_to_char_offset(line_o, frame.colno)
                            off_end = byte_offset_to_char_offset(
                                line_o, frame.end_colno
                            )

                            # A bunch of caret '^' characters under the error location.
                            anchors = (
                                " " * (off_start - stripped_chars - 1)
                            ) + "^" * len(
                                line_o[off_start:off_end].replace(
                                    "\t", " " * dump_tab_width
                                )
                            )

                            trace_dump += f'\n{" " * (dump_tab_width * 2)}{anchors}'

                    trace_dump += f'\n{" " * dump_tab_width}at {func_signature} {frame.filename}:{frame.lineno}'

                print(trace_dump)  # FIXME: Dump to stderr with some logging api.
                return None

    return module


def create_jac_py_module(
    mod_bundle: Optional[Module | str],
    module_name: str,
    package_path: str,
    full_target: str,
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
) -> types.ModuleType:
    """Import a Python module."""
    try:
        if target.startswith("."):
            target = target.lstrip(".")
            full_target = path.normpath(path.join(caller_dir, target))
            spec = importlib.util.spec_from_file_location(target, full_target + ".py")
            if spec and spec.loader:
                imported_module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = imported_module
                spec.loader.exec_module(imported_module)
            else:
                raise ImportError(f"Cannot find module {target} at {full_target}")
        else:
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
        return imported_module
    except ImportError as e:
        print(f"Failed to import module {target}")
        raise e
