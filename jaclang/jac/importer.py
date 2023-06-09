"""Special Imports for Jac Code."""
import inspect
import sys
import traceback
import types
from os import makedirs, path
from typing import Callable, Optional

from jaclang.jac.transpiler import transpile_jac_blue, transpile_jac_purple
from jaclang.jac.utils import add_line_numbers, clip_code_section


def import_jac_module(
    transpiler_func: Callable,
    target: str,
    base_path: Optional[str] = None,
    save_file: bool = False,
) -> Optional[types.ModuleType]:
    """Core Import Process."""
    target = path.join(*(target.split("."))) + ".jac"

    dir_path, file_name = path.split(target)
    module_name = path.splitext(file_name)[0]
    package_path = dir_path.replace(path.sep, ".")

    if package_path and f"{package_path}.{module_name}" in sys.modules:
        return sys.modules[f"{package_path}.{module_name}"]
    elif not package_path and module_name in sys.modules:
        return sys.modules[module_name]

    if base_path:
        caller_dir = path.dirname(base_path) if not path.isdir(base_path) else base_path
    else:
        frame = inspect.stack()[2]
        caller_dir = path.dirname(path.abspath(frame[0].f_code.co_filename))
    full_target = path.normpath(path.join(caller_dir, target))

    code_string = transpiler_func(file_path=full_target, base_dir=caller_dir)
    with open(full_target, 'r') as file:
        jac_code_string = file.read()
    # if save_file:
    dev_dir = path.join(caller_dir, "__jac_gen__")
    makedirs(dev_dir, exist_ok=True)
    with open(path.join(dev_dir, module_name + ".py"), "w") as f:
        f.write(code_string)

    module = types.ModuleType(module_name)
    module.__file__ = full_target
    module.__name__ = module_name

    try:
        exec(code_string, module.__dict__)
    except Exception as e:
        traceback.print_exc()
        tb = traceback.extract_tb(e.__traceback__)
        except_line = list(tb)[-1].lineno

        py_error_region = clip_code_section(add_line_numbers(code_string), except_line, 3)
        jac_err_line = int(code_string.splitlines()[except_line].split()[-1])
        jac_code_region = clip_code_section(add_line_numbers(jac_code_string), jac_err_line, 3)
        print(
            f"Error in module {module_name}\nJac file: {full_target}\n"
            f"Error: {str(e)}\nPyCode:\n{py_error_region}\n"
            f"JacCode (incorrect at the moment):\n{jac_code_region}\n"
        )
        return None

    if package_path:
        parts = package_path.split(".")
        for i in range(len(parts)):
            package_name = ".".join(parts[: i + 1])
            if package_name not in sys.modules:
                sys.modules[package_name] = types.ModuleType(package_name)

        setattr(sys.modules[package_path], module_name, module)
        sys.modules[f"{package_path}.{module_name}"] = module
    else:
        sys.modules[module_name] = module

    return module


def jac_blue_import(
    target: str, base_path: Optional[str] = None, save_file: bool = False
) -> Optional[types.ModuleType]:
    """Jac Blue Imports."""
    return import_jac_module(transpile_jac_blue, target, base_path, save_file)


def jac_purple_import(
    target: str, base_path: Optional[str] = None, save_file: bool = False
) -> Optional[types.ModuleType]:
    """Jac Purple Imports."""
    return import_jac_module(transpile_jac_purple, target, base_path, save_file)
