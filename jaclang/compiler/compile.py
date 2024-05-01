"""Transpilation functions."""

import os
import pickle
import copy
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
    disable_cache_saving: bool = False
) -> Pass:
    """Convert a Jac file to an AST."""
    with open(file_path) as file:
        return jac_str_to_pass(
            jac_str=file.read(),
            file_path=file_path,
            target=target,
            schedule=schedule,
            use_cache=use_cache,
            disable_cache_saving=disable_cache_saving
        )


def jac_str_to_pass(
    jac_str: str,
    file_path: str,
    target: Optional[Type[Pass]] = None,
    schedule: list[Type[Pass]] = pass_schedule,
    use_cache: bool = False,
    disable_cache_saving: bool = False
) -> Pass:
    """Convert a Jac file to an AST."""
    if not target:
        target = schedule[-1]
    source = ast.JacSource(jac_str, mod_path=file_path)
    ast_ret = JacParser(input_ir=source)

    use_cache = "JAC_ENABLE_CACHE" in os.environ

    # Checking if there is a module changed
    if not use_cache:
        ast_ret = jac_run_passes(ast_ret, target, schedule)
        return ast_ret
    
    print_incremental_flow_usage()
    modules = __get_all_modules(ast_ret.ir)

    module = modules[0]
    if os.path.exists(f"{module.name}.jacache"):
        # with open(f"{module.name}.jacache", "rb") as cache_file:
        #     cache = pickle.load(cache_file)
        # if cache["checksum"] == module.checksum:
        #     debug_print(f"Using jacache for module '{module.name}'")
        #     ast_ret.ir = cache["ast"]
        #     # for warning, t_node in cache["warnings_had"]:
        #     #     ast_ret.log_warning(warning.msg, t_node)
        # else:
        #     debug_print(
        #         f"Module '{module.name}' checksum is changed, compiling the module..."
        #     )
        #     ast_ret = jac_run_passes(ast_ret, target, schedule)
        #     if not disable_cache_saving: jac_save_ast(ast_ret)
        ast_ret.ir = jac_load_module(module.name)
    else:
        debug_print(
            f"Module '{module.name}' is not found in the cache, compiling the module..."
        )
        ast_ret = jac_run_passes(ast_ret, target, schedule)
        if not disable_cache_saving: jac_save_ast(ast_ret)

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

graph = dict[ast.AstNode | None, list[ast.AstNode]]

def jac_save_ast(jac_pass: Pass) -> None:
    """Save jac ast into a cache file."""
    dep_graph = jac_compute_dep_graph(jac_pass)
    jac_save_module(None, dep_graph)


def jac_compute_dep_graph(jac_pass: Pass) -> graph:
    ir = copy.deepcopy(jac_pass.ir)
    dep_graph: dict[ast.AstNode, list[ast.AstNode]] = {}
    for m in __get_all_modules(ir):
        parent: ast.AstNode = m.parent
        while not isinstance(parent, ast.Module | None):
            parent = parent.parent
        if parent not in dep_graph: 
            dep_graph[parent] = []
        dep_graph[parent].append(m)
    return dep_graph

def jac_save_module(module: ast.Module| None, dep_graph: graph):
    for m in dep_graph[module]:
        if m in dep_graph: jac_save_module(m, dep_graph)
        debug_print("Saving module", m.name)
        depends_on: dict[str, ast.AstNode] =  {}
        if m in dep_graph:
            depends_on: dict[str, ast.AstNode] = {i.name: i.parent for i in dep_graph[m]}
            for dep_module in dep_graph[m]:
                dep_module_index = dep_module.parent.kid.index(dep_module)
                dep_module.parent.kid[dep_module_index] = ast.String(
                    "", 
                    f"__custom_jac_marker__{dep_module.name}",
                    f"__custom_jac_marker__{dep_module.name}",
                    0, 0, 0, 0, 0
                )
                print(f"Removing {dep_module.name} from {m.name}")

        # warning_had = []
        # # for i in jac_pass.warnings_had:
        # #     temp_node = ast.Token("", "", "", 0, 0, 0, 0, 0)
        # #     temp_node.loc = i.loc
        # #     warning_had.append((i, temp_node))
        print(depends_on)
        out = {
            "name": m.name,
            "checksum": m.checksum,
            "ast": m,
            "depends_on": depends_on,
            # "warnings_had": warning_had,
        }
        with open(f"{m.name}.jacache", "wb") as f:
            f.write(pickle.dumps(out))

def jac_load_module(module_name: str) -> ast.Module:
    with open(f"{module_name}.jacache", "rb") as cache_file:
        cache = pickle.load(cache_file)
    
    ir: ast.Module = cache["ast"]

    for mod_name in cache["depends_on"]:
        parent = cache["depends_on"][mod_name]
        place_holder = None
        for k in parent.kid:
            if k.value.startswith("__custom_jac_marker__"):
                place_holder = k
                break
        parent.kid[parent.kid.index(place_holder)] = jac_load_module(mod_name)
    
    debug_print("Loaded module", cache["name"])
    return ir

    # if cache["checksum"] == module.checksum:
    #     debug_print(f"Using jacache for module '{module.name}'")
    #     ast_ret.ir = cache["ast"]


def __get_all_modules(ir: ast.AstNode) -> list[ast.Module]:
    modules: list[ast.Module] = []
    if isinstance(ir, ast.Module):
        modules.append(ir)
    modules += ir.get_all_sub_nodes(ast.Module, brute_force=True)
    return modules

incr_flow_usage_printed: bool = False
def print_incremental_flow_usage():
    global incr_flow_usage_printed
    if not incr_flow_usage_printed:
        debug_print("***************************************************")
        debug_print("******* Jac Incremental Compilation Enabled *******")
        debug_print("***************************************************")
        incr_flow_usage_printed = True