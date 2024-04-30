"""Transpilation functions."""

import os
import pickle
from typing import Any, Optional, Sequence, Type

import jaclang.compiler.absyntree as ast
from jaclang.compiler.parser import JacParser
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main import PyOutPass, pass_schedule
from jaclang.compiler.passes.tool import JacFormatPass
from jaclang.compiler.passes.tool.schedules import format_pass


def debug_print(*args: Sequence[Any]) -> None:
    """Debug print for jacache feature, enable it be adding JAC_CACHE_DEBUG in env."""
    if "JAC_CACHE_DEBUG" in os.environ:
        print("INFO -", *args)


def compile_jac(file_path: str, cache_result: bool = False) -> Pass:
    """Start Compile for Jac file and return python code as string."""
    code = jac_file_to_pass(
        file_path=file_path,
        schedule=pass_schedule,
    )
    if cache_result and isinstance(code.ir, ast.Module):
        print_pass = PyOutPass(input_ir=code.ir, prior=code)
        return print_pass
    else:
        return code


def jac_file_to_pass(
    file_path: str,
    target: Optional[Type[Pass]] = None,
    schedule: list[Type[Pass]] = pass_schedule,
    use_cache: bool = False,
) -> Pass:
    """Convert a Jac file to an AST."""
    with open(file_path) as file:
        return jac_str_to_pass(
            jac_str=file.read(),
            file_path=file_path,
            target=target,
            schedule=schedule,
            use_cache=use_cache,
        )


def jac_str_to_pass(
    jac_str: str,
    file_path: str,
    target: Optional[Type[Pass]] = None,
    schedule: list[Type[Pass]] = pass_schedule,
    use_cache: bool = False,
) -> Pass:
    """Convert a Jac file to an AST."""
    if not target:
        target = schedule[-1]
    source = ast.JacSource(jac_str, mod_path=file_path)
    ast_ret = JacParser(input_ir=source)

    use_cache = "JAC_ENABLE_CACHE" in os.environ

    # Checking if there is a module changed
    if use_cache:
        debug_print("***************************************************")
        debug_print("******* Jac Incremental Compilation Enabled *******")
        debug_print("***************************************************")
        modules = __get_all_modules(ast_ret.ir)
        if len(modules) > 1:
            debug_print("Jac cache only works in case of single module")
            ast_ret = jac_run_passes(ast_ret, target, schedule)
        else:
            module = modules[0]
            if os.path.exists(f"{module.name}.jacache"):
                with open(f"{module.name}.jacache", "rb") as cache_file:
                    cache = pickle.load(cache_file)
                if cache["checksum"] == module.checksum:
                    debug_print(f"Using jacache for module '{module.name}'")
                    ast_ret.ir = cache["ast"]
                    for warning in cache["warnnings_had"]:
                        ast_ret.log_warning(str(warning))
                else:
                    debug_print(
                        f"Module '{module.name}' checksum is changed, compiling the module..."
                    )
                    ast_ret = jac_run_passes(ast_ret, target, schedule)
                    jac_save_ast(ast_ret)
            else:
                debug_print(
                    f"Module '{module.name}' is not found in the cache, compiling the module..."
                )
                ast_ret = jac_run_passes(ast_ret, target, schedule)
                jac_save_ast(ast_ret)
    else:
        ast_ret = jac_run_passes(ast_ret, target, schedule)

    return ast_ret


def jac_run_passes(
    parser_ast: JacParser, target: Pass, schedule: list[Type[Pass]]
) -> Pass:
    """Run jac passes on jac parser output."""
    for i in schedule:
        if i == target:
            break
        parser_ast = i(input_ir=parser_ast.ir, prior=parser_ast)
    return target(input_ir=parser_ast.ir, prior=parser_ast)


def jac_pass_to_pass(
    in_pass: Pass,
    target: Optional[Type[Pass]] = None,
    schedule: list[Type[Pass]] = pass_schedule,
) -> Pass:
    """Convert a Jac file to an AST."""
    if not target:
        target = schedule[-1]
    ast_ret = in_pass
    for i in schedule:
        if i == target:
            break
        ast_ret = i(input_ir=ast_ret.ir, prior=ast_ret)
    ast_ret = target(input_ir=ast_ret.ir, prior=ast_ret)
    return ast_ret


def jac_file_formatter(
    file_path: str,
    schedule: list[Type[Pass]] = format_pass,
) -> JacFormatPass:
    """Convert a Jac file to an AST."""
    target = JacFormatPass
    with open(file_path) as file:
        source = ast.JacSource(file.read(), mod_path=file_path)
        prse: Pass = JacParser(input_ir=source)
    for i in schedule:
        if i == target:
            break
        prse = target(input_ir=prse.ir, prior=prse)
    prse = target(input_ir=prse.ir, prior=prse)
    return prse


def jac_save_ast(jac_pass: Pass) -> None:
    """Save jac ast into a cache file."""
    ir = jac_pass.ir
    modules: list[ast.Module] = __get_all_modules(ir)
    for m in modules:
        debug_print("Saving module", m.name)
        out = {
            "name": m.name,
            "checksum": m.checksum,
            "ast": m,
            "warnnings_had": jac_pass.warnings_had,
        }
        with open(f"{m.name}.jacache", "wb") as f:
            f.write(pickle.dumps(out))


def __get_all_modules(ir: ast.AstNode) -> list[ast.Module]:
    modules: list[ast.Module] = []
    if isinstance(ir, ast.Module):
        modules.append(ir)
    modules += ir.get_all_sub_nodes(ast.Module)
    return modules


# M0
# M1 & M2
