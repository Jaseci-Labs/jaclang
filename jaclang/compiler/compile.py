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
from jaclang.compiler.passes.main.sub_node_tab_pass import SubNodeTabPass


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
    use_cache: bool = True,
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
    use_cache: bool = True,
    disable_cache_saving: bool = False
) -> Pass:
    """Convert a Jac file to an AST."""
    if not target:
        target = schedule[-1]
    source = ast.JacSource(jac_str, mod_path=file_path)
    ast_ret = JacParser(input_ir=source)

    use_cache_flag = "JAC_ENABLE_CACHE" in os.environ
    use_cache = use_cache and use_cache_flag

    if not use_cache:
        ast_ret = jac_run_passes(ast_ret, target, schedule)
    else:
        ast_ret = jac_incr_compile(ast_ret, target, schedule, disable_cache_saving)    
    
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


###############################
### Incremental Compilation ###
###############################
graph = dict[ast.AstNode | None, list[ast.Module]]
incr_flow_usage_printed: bool = False


def print_incremental_flow_usage():
    """Print that incremental compilation is been in use"""
    global incr_flow_usage_printed
    if not incr_flow_usage_printed:
        debug_print("***************************************************")
        debug_print("******* Jac Incremental Compilation Enabled *******")
        debug_print("***************************************************")
        incr_flow_usage_printed = True


def debug_print(*args: Sequence[Any]) -> None:
    """Debug print for jacache feature, enable it be adding JAC_CACHE_DEBUG in env."""
    if "JAC_CACHE_DEBUG" in os.environ:
        print("INFO -", *args)


def jac_incr_compile(
    ast_ret: JacParser, 
    target: Pass, 
    schedule: list[Type[Pass]],
    disable_cache_saving: bool
) -> Pass:
    """Incremental compilation main execution"""
    # This function will be called multiple time once per module, we need to 
    # ignore all calls from import_pass as it only loads the module jac ast
    # before doing the other passes

    print_incremental_flow_usage()
    modules = __get_all_modules(ast_ret.ir)

    module = modules[0]
    if os.path.exists(f"{module.name}.jacache"):
        ast_ret.ir, incr_loaded, w_had = jac_load_module(module.name)
        
        if not incr_loaded:
            ast_ret = jac_run_passes(ast_ret, target, schedule)
            jac_save_ast(ast_ret)
        else:
            for w in w_had:
                ast_ret.log_warning(str(w[0].msg), w[1])
    else:
        debug_print(
            f"Module '{module.name}' is not found in the cache, compiling the module..."
        )
        ast_ret = jac_run_passes(ast_ret, target, schedule)    
        if not disable_cache_saving: jac_save_ast(ast_ret)
    
    return ast_ret


def jac_save_ast(jac_pass: Pass) -> None:
    """Save jac ast into cache files."""
    dep_graph = jac_compute_dep_graph(jac_pass)
    jac_save_module(None, dep_graph, jac_pass)


def jac_compute_dep_graph(jac_pass: Pass) -> graph:
    """Compute all the dependencies between all the modules"""
    ir = copy.deepcopy(jac_pass.ir)
    dep_graph: dict[ast.AstNode, list[ast.AstNode]] = {}
    
    for m in __get_all_modules(ir):
        # Go up in the ast until we find the parent module OR None
        # in case of that module is a top main module
        parent: ast.AstNode = m.parent
        while not isinstance(parent, ast.Module | None):
            parent = parent.parent
        
        if parent not in dep_graph: 
            dep_graph[parent] = []
        dep_graph[parent].append(m)

    return dep_graph


def jac_save_module(
    module: ast.Module| None, 
    dep_graph: graph, 
    jac_pass: Pass
):
    """Save a single module in the dependency graph"""
    for m in dep_graph[module]:
        
        # Save all the dependencies of the module
        if m in dep_graph: 
            jac_save_module(m, dep_graph, jac_pass)
        
        # if m.incr_loaded: return 

        debug_print("Saving module", m.name)
        depends_on: dict[str, ast.AstNode] =  {}
        
        # Replace module dependencies nodes with a marker nodes
        # Keep track of the dependencies in a separate hash that
        # contains module name and module parent to be used in module
        # loading
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

        # Save all mypy warnings related to the current module being saved
        warning_had = []
        for i in jac_pass.warnings_had:
            if i.loc.mod_path == m.loc.mod_path:
                temp_node = ast.Token("", "", "", 0, 0, 0, 0, 0)
                temp_node.loc = i.loc
                warning_had.append((i, temp_node))

        # TODO: Remove all items that link to other nodes
        # example: remove the parent as it links to a node that 
        # doesn't need to be saved and we can't use it in next run
        t_parent = m.parent
        m.parent = None
        out = {
            "name": m.name,
            "checksum": m.checksum,
            "ast": m,
            "depends_on": depends_on,
            "warnings_had": warning_had,
        }
        with open(f"{m.name}.jacache", "wb") as f:
            f.write(pickle.dumps(out))
        m.parent = t_parent

def jac_load_module(module_name: str) -> tuple[ast.Module, bool, list]:
    """Load jacache file"""
    debug_print(f"Using jacache for module '{module_name}'")
    with open(f"{module_name}.jacache", "rb") as cache_file:
        cache = pickle.load(cache_file)
    
    ir: ast.Module = cache["ast"]
    original_module = jac_file_to_pass(
        ir.loc.mod_path,
        target=SubNodeTabPass, 
        disable_cache_saving=True,
        use_cache=False
    ).ir

    assert isinstance(original_module, ast.Module)

    # TODO: calculate checksum from the file directly instead of depending on
    # ast.Module
    if original_module.checksum == ir.checksum:
        ir.incr_loaded = True

        for mod_name in cache["depends_on"]:
            parent = cache["depends_on"][mod_name]
            place_holder = None
            for k in parent.kid:
                if k.value.startswith("__custom_jac_marker__"):
                    place_holder = k
                    break
            place_holder_index = parent.kid.index(place_holder)
            parent.kid[place_holder_index], incr_loaded, w_had = jac_load_module(mod_name)
            cache["warnings_had"] += w_had
            parent.kid[place_holder_index].parent = parent
            ir.incr_loaded = True and incr_loaded
    
        debug_print("Loaded module", cache["name"])
    
    else:
        
        # TODO: Check what else needs to be done when I create the module here
        # example: I needed to link the module parent as by default it's None
        original_module.parent = ir.parent
        ir = original_module
        debug_print("Compiling module", cache["name"], "...")

    return ir, ir.incr_loaded, cache["warnings_had"]


def __get_all_modules(ir: ast.AstNode) -> list[ast.Module]:
    modules: list[ast.Module] = []
    if isinstance(ir, ast.Module):
        modules.append(ir)
    for m in ir.kid:
        modules += __get_all_modules(m)
    return modules


## TODO
## All places that we store the nodes needs to be re-evaluated as they store the old nodes