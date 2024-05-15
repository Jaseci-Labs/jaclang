"""Abstract class for IR Passes for Jac."""

from abc import ABC, abstractmethod

from typing import Optional, Type, Dict, Any, TypeVar
from collections import defaultdict

import copy
import pickle
import subprocess
import os

from jaclang.settings import settings
import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes.transform import Transform
from jaclang.utils.helpers import pascal_to_snake

T = TypeVar("T", bound=ast.AstNode)


class Pass(Transform[T]):
    """Abstract class for IR passes."""

    def __init__(self, input_ir: T, prior: Optional[Transform]) -> None:
        """Initialize parser."""
        self.term_signal = False
        self.prune_signal = False
        self.ir: ast.AstNode = input_ir
        Transform.__init__(self, input_ir, prior)

    def before_pass(self) -> None:
        """Run once before pass."""
        pass

    def after_pass(self) -> None:
        """Run once after pass."""
        pass

    def enter_node(self, node: ast.AstNode) -> None:
        """Run on entering node."""
        if hasattr(self, f"enter_{pascal_to_snake(type(node).__name__)}"):
            getattr(self, f"enter_{pascal_to_snake(type(node).__name__)}")(node)

    def exit_node(self, node: ast.AstNode) -> None:
        """Run on exiting node."""
        if hasattr(self, f"exit_{pascal_to_snake(type(node).__name__)}"):
            getattr(self, f"exit_{pascal_to_snake(type(node).__name__)}")(node)

    def terminate(self) -> None:
        """Terminate traversal."""
        self.term_signal = True

    def prune(self) -> None:
        """Prune traversal."""
        self.prune_signal = True

    @staticmethod
    def get_all_sub_nodes(
        node: ast.AstNode, typ: Type[T], brute_force: bool = False
    ) -> list[T]:
        """Get all sub nodes of type."""
        result: list[T] = []
        # Assumes pass built the sub node table
        if not node:
            return result
        elif len(node._sub_node_tab):
            if typ in node._sub_node_tab:
                for i in node._sub_node_tab[typ]:
                    if isinstance(i, typ):
                        result.append(i)
        elif len(node.kid):
            if not brute_force:
                raise ValueError(f"Node has no sub_node_tab. {node}")
            # Brute force search
            else:
                for i in node.kid:
                    if isinstance(i, typ):
                        result.append(i)
                    result.extend(Pass.get_all_sub_nodes(i, typ, brute_force))
        return result

    @staticmethod
    def has_parent_of_type(node: ast.AstNode, typ: Type[T]) -> Optional[T]:
        """Check if node has parent of type."""
        while node.parent:
            if isinstance(node.parent, typ):
                return node.parent
            node = node.parent
        return None

    @staticmethod
    def has_parent_of_node(node: ast.AstNode, parent: ast.AstNode) -> bool:
        """Check if node has parent of type."""
        while node.parent:
            if node.parent == parent:
                return True
            node = node.parent
        return False

    def recalculate_parents(self, node: ast.AstNode) -> None:
        """Recalculate parents."""
        if not node:
            return
        for i in node.kid:
            if i:
                i.parent = node
                self.recalculate_parents(i)

    # Transform Implementations
    # -------------------------
    def transform(self, ir: T) -> ast.AstNode:
        """Run pass."""
        # Only performs passes on proper ASTs
        if not isinstance(ir, ast.AstNode):
            return ir
        self.before_pass()
        if not isinstance(ir, ast.AstNode):
            raise ValueError("Current node is not an AstNode.")
        self.traverse(ir)
        self.after_pass()
        return self.ir

    def traverse(self, node: ast.AstNode) -> ast.AstNode:
        """Traverse tree."""
        if self.term_signal:
            return node
        self.cur_node = node
        self.enter_node(node)
        if not self.prune_signal:
            for i in node.kid:
                if i:
                    self.traverse(i)
        else:
            self.prune_signal = False
        self.cur_node = node
        self.exit_node(node)
        return node

    def update_code_loc(self, node: Optional[ast.AstNode] = None) -> None:
        """Update code location."""
        if node is None:
            node = self.cur_node
        if not isinstance(node, ast.AstNode):
            self.ice("Current node is not an AstNode.")

    def error(self, msg: str, node_override: Optional[ast.AstNode] = None) -> None:
        """Pass Error."""
        self.update_code_loc(node_override)
        self.log_error(f"{msg}", node_override=node_override)

    def warning(self, msg: str, node_override: Optional[ast.AstNode] = None) -> None:
        """Pass Error."""
        self.update_code_loc(node_override)
        self.log_warning(f"{msg}", node_override=node_override)

    def ice(self, msg: str = "Something went horribly wrong!") -> RuntimeError:
        """Pass Error."""
        self.log_error(f"ICE: Pass {self.__class__.__name__} - {msg}")
        return RuntimeError(
            f"Internal Compiler Error: Pass {self.__class__.__name__} - {msg}"
        )


class PrinterPass(Pass):
    """Printer Pass for Jac AST."""

    def enter_node(self, node: ast.AstNode) -> None:
        """Run on entering node."""
        print("Entering:", node)
        super().enter_node(node)

    def exit_node(self, node: ast.AstNode) -> None:
        """Run on exiting node."""
        super().exit_node(node)
        print("Exiting:", node)


class CacheablePass(ABC):
    """Implement the cache functionality in the passes"""

    # This class functionality is to call the cache_module function
    # for each module in the tree after removing all sub modules in 
    # the tree

    Graph = dict[ast.Module | None, list[ast.Module]]

    # # Abstract methods to be implemented
    # @abstractmethod
    # def cache_module(self, mod: ast.Module) -> dict:
    #     """Create a cache for a module."""
    #     pass
    
    # @abstractmethod
    # def load_module(self, cache: ast.Module, mod: ast.Module = None) -> None:
    #     """Load a cache for a module."""
    #     pass

    # Class functionality
    def __compute_dep_graph(self) -> Graph:
        """Compute all the dependencies between all the modules"""
        
        dep_graph: dict[ast.AstNode, list[ast.AstNode]] = defaultdict(list)
        ir_copy = copy.deepcopy(self.ir)  # copying it as we will do some changes in the nodes
        
        for m in self.__get_all_nodes(ir_copy):
            # Go up in the ast until we find the parent module OR None
            # in case of that module is a top main module
            parent: ast.AstNode = m.parent
            while not isinstance(parent, ast.Module | None):
                parent = parent.parent

            dep_graph[parent].append(m)
        
        return dep_graph
    
    ## TODO: Make a new node type for the module placeholder
    ## TODO: Optimize the way to search for placeholders
    def __detach_modules(self, graph: Graph):
        """Breaking the tree of the modules"""
        for m in graph:
            if m is None: continue
            for sub_m in graph[m]:
                # For each sub module we need to 
                #   1- Remove it from parent kids
                #   2- Add a marker to its' location
                #   3- Remove the parent 
                sub_module_index = sub_m.parent.kid.index(sub_m)
                sub_m.parent.kid[sub_module_index] = ast.String(
                    "", 
                    f"__custom_jac_marker__{sub_m.name}",
                    f"__custom_jac_marker__{sub_m.name}",
                    0, 0, 0, 0, 0
                )
                sub_m.parent.kid[sub_module_index].parent = sub_m.parent
                sub_m.parent = None
    
    def __connect_modules(self, top_mod: ast.Module, child_mod: ast.Module):
        """Connecting the modules into the tree"""
        marker_nodes = self.__get_all_nodes(top_mod, ast.String)
        marker = None
        for i in marker_nodes:
            if i.value == "__custom_jac_marker__" + child_mod.name:
                marker = i
        marker_index = marker.parent.kid.index(marker)
        marker.parent.kid[marker_index] = child_mod
        child_mod.parent = marker.parent
        marker.parent = None
    
    def __get_all_nodes(self, ir: ast.AstNode, node_type = ast.Module) -> list[ast.AstNode]:
        out = set()
        for i in ir.kid:
            out |= self.__get_all_nodes(i, node_type)
        if isinstance(ir, node_type):
            out.add(ir)
        return out

    def __get_file_checksum(self, path: str) -> str:
        """Calculate the checksum of a file"""
        result = subprocess.run(['md5sum', path], stdout=subprocess.PIPE)
        checksum = result.stdout.decode().split()[0]
        return checksum
    
    def __save_module(self, mod: ast.Module, dep_graph: Graph):
        cache = {
            "ast": mod,
            "DependsOn": [] if mod not in dep_graph else [i.name for i in dep_graph[mod]],
            "ModuleName": mod.name,
            "Checksum": self.__get_file_checksum(mod.loc.mod_path)
        }
        with open(f"{self.__class__.__name__}__{mod.name}.jacache", "wb") as f:
            f.write(pickle.dumps(cache))
    
    ## Limitation in loading module
    ##  1- if a module is changed then the module with all it's children will be reloaded
    ##      - Work on only loading the changed module
    ##  2- Reload the _sub_node_tab when a module is loaded
    def __load_module(self, mod_name: str) -> ast.Module | None:
        if not os.path.isfile(f"{self.__class__.__name__}__{mod_name}.jacache"):
            return None
        
        print("Loading module", mod_name)
        with open(f"{self.__class__.__name__}__{mod_name}.jacache", "rb") as f:
            mod_cache = pickle.loads(f.read())
        
        for mod in mod_cache["DependsOn"]:
            sub_mod = self.__load_module(mod)
            if sub_mod:
                self.__connect_modules(mod_cache["ast"], sub_mod)
        
        current_version_checksum = self.__get_file_checksum(mod_cache["ast"].loc.mod_path)
        if mod_cache["Checksum"] != current_version_checksum:
            return None
        
        ## Calculate _sub_node_tab here
        return mod_cache["ast"]
        
        
    
    def cache(self) -> None:
        """Call cache_module on each module after detaching them"""
        # This functions offer the following the caching functionality
        # by computing the modules dependencies and detaching the modules
        # then cache the result of cache_module with some other metadata like
        # checksum and the module dependencies 

        graph = self.__compute_dep_graph()
        self.__detach_modules(graph)
        for mod in [j for m in graph.values() for j in m]:
           self.__save_module(mod, graph)
    
    def load_cache(self, top_mod: ast.Module) -> None:
        self.__load_module(top_mod.name)
        exit()
        



# def jac_save_module(
#     module: ast.Module| None, 
#     dep_graph: graph, 
#     jac_pass: Pass
# ):
#     """Save a single module in the dependency graph"""
#     for m in dep_graph[module]:
        
#         # Save all the dependencies of the module
#         if m in dep_graph: 
#             jac_save_module(m, dep_graph, jac_pass)
        
#         # if m.incr_loaded: return 

#         debug_print("Saving module", m.name)
#         depends_on: dict[str, ast.AstNode] =  {}
        
#         # Replace module dependencies nodes with a marker nodes
#         # Keep track of the dependencies in a separate hash that
#         # contains module name and module parent to be used in module
#         # loading
#         if m in dep_graph:
#             depends_on: dict[str, ast.AstNode] = {i.name: i.parent for i in dep_graph[m]}
#             for dep_module in dep_graph[m]:
#                 dep_module_index = dep_module.parent.kid.index(dep_module)
#                 dep_module.parent.kid[dep_module_index] = ast.String(
#                     "", 
#                     f"__custom_jac_marker__{dep_module.name}",
#                     f"__custom_jac_marker__{dep_module.name}",
#                     0, 0, 0, 0, 0
#                 )

#         # Save all mypy warnings related to the current module being saved
#         warning_had = []
#         for i in jac_pass.warnings_had:
#             if i.loc.mod_path == m.loc.mod_path:
#                 temp_node = ast.Token("", "", "", 0, 0, 0, 0, 0)
#                 temp_node.loc = i.loc
#                 warning_had.append((i, temp_node))

#         # TODO: Remove all items that link to other nodes
#         # example: remove the parent as it links to a node that 
#         # doesn't need to be saved and we can't use it in next run
#         t_parent = m.parent
#         m.parent = None
#         out = {
#             "name": m.name,
#             "checksum": m.checksum,
#             "ast": m,
#             "depends_on": depends_on,
#             "warnings_had": warning_had,
#         }
#         with open(f"{m.name}.jacache", "wb") as f:
#             f.write(pickle.dumps(out))
#         m.parent = t_parent

# def jac_load_module(module_name: str) -> tuple[ast.Module, bool, list]:
#     """Load jacache file"""
#     debug_print(f"Using jacache for module '{module_name}'")
#     with open(f"{module_name}.jacache", "rb") as cache_file:
#         cache = pickle.load(cache_file)
    
#     ir: ast.Module = cache["ast"]
#     original_module = jac_file_to_pass(
#         ir.loc.mod_path,
#         target=SubNodeTabPass, 
#         disable_cache_saving=True,
#         use_cache=False
#     ).ir

#     assert isinstance(original_module, ast.Module)

#     # TODO: calculate checksum from the file directly instead of depending on
#     # ast.Module
#     if original_module.checksum == ir.checksum:
#         ir.incr_loaded = True

#         for mod_name in cache["depends_on"]:
#             parent = cache["depends_on"][mod_name]
#             place_holder = None
#             for k in parent.kid:
#                 if k.value.startswith("__custom_jac_marker__"):
#                     place_holder = k
#                     break
#             place_holder_index = parent.kid.index(place_holder)
#             parent.kid[place_holder_index], incr_loaded, w_had = jac_load_module(mod_name)
#             cache["warnings_had"] += w_had
#             parent.kid[place_holder_index].parent = parent
#             ir.incr_loaded = True and incr_loaded
    
#         debug_print("Loaded module", cache["name"])
    
#     else:
        
#         # TODO: Check what else needs to be done when I create the module here
#         # example: I needed to link the module parent as by default it's None
#         original_module.parent = ir.parent
#         ir = original_module
#         debug_print("Compiling module", cache["name"], "...")

#     return ir, ir.incr_loaded, cache["warnings_had"]

