"""Utility functions for the language server."""

import:py asyncio ;
import:py builtins ;
import:py importlib.util ;
import:py os ;
import:py re ;
import:py sys ;
import:py from functools, wraps ;
import:py from typing, Any, Awaitable, Callable, Coroutine, Optional, ParamSpec, TypeVar ;
import:py jaclang.compiler.absyntree as ast ;
import:py from jaclang.compiler.codeloc, CodeLocInfo ;
import:py from jaclang.compiler.constant, SymbolType ;
import:py from jaclang.compiler.symtable, Symbol, SymbolTable ;
import:py from jaclang.utils.helpers, import_target_to_relative_path ;
import:py lsprotocol.types as lspt ;

with entry {
    T = TypeVar(
        "T",
        bound=Callable[(..., Coroutine[(Any, Any, Any)])] 
    );    
    P = ParamSpec("P");
}

can debounce(wait: float) -> Callable[[T], Callable[(..., Awaitable[None])]] {
    """Debounce decorator for async functions.""" ;    
    can decorator(fn: T) -> Callable[..., Awaitable[None]] {
        @ wraps(fn) 
         async can debounced(*args: P.args, **kwargs: P.kwargs) -> None {
            async can call_it() -> None {
                awaitfn(*args, _=kwargs) ;
            }
            
            if hasattr(debounced, "_task") {
                debounced._task.cancel() ;}
            
            async can debounced_coro() -> None {
                try  {
                    awaitasyncio.sleep(wait) ;    
                    awaitcall_it() ;} except asyncio.CancelledError {;
                }
            }
            
            setattr(
                debounced,
                "_task",
                asyncio.create_task(debounced_coro())
            ) ;
        }
        
        return debounced ;
    }
    
    return decorator ;
}

can sym_tab_list(sym_tab: SymbolTable, file_path: str) -> list[SymbolTable] {
    """Iterate through symbol table.""" ;    
    sym_tabs = [sym_tab] if not isinstance(sym_tab.owner, ast.Module)
        and sym_tab.owner.loc.mod_path != file_path else [];    
    for i in sym_tab.kid {
        sym_tabs += sym_tab_list(i, file_path=file_path);
    }
    
    return sym_tabs ;
}

can find_deepest_symbol_node_at_pos(node: ast.AstNode, line: int, character: int) -> Optional[ast.AstSymbolNode] {
    """Return the deepest symbol node that contains the given position.""" ;    
    last_symbol_node = None;    
    if position_within_node(node, line, character) {
        if isinstance(node, ast.AstSymbolNode) {
            last_symbol_node = node;}
        
        for child in [i for i in node.kid if i.loc.mod_path == node.loc.mod_path] {
            if position_within_node(child, line, character) {
                deeper_node = find_deepest_symbol_node_at_pos(child, line, character);    
                if deeper_node is not None {
                    last_symbol_node = deeper_node;}
            }
        }
    }
    
    return last_symbol_node ;
}

can position_within_node(node: ast.AstNode, line: int, character: int) -> bool {
    """Check if the position falls within the node's location.""" ;    
    if node.loc.first_line < (line + 1)< node.loc.last_line {
        return True ;}
    
    if node.loc.first_line == (line + 1)
        and node.loc.col_start <= (character + 1)
        and node.loc.last_line == (line + 1)
        and node.loc.col_end >= (character + 1)
        or node.loc.last_line > (line + 1) {
        return True ;}
    
    if node.loc.last_line == (line + 1)
        and node.loc.col_start <= (character + 1)<= node.loc.col_end {
        return True ;}
    
    return False ;
}

can collect_symbols(node: SymbolTable) -> list[lspt.DocumentSymbol] {
    """Recursively collect symbols from the AST.""" ;    
    symbols = [];    
    if node is None {
        return symbols ;}
    
    for (key, item) in node.tab.items() {
        if key in dir(builtins)
            or item in [owner_sym(tab) for tab in node.kid]
            or item.decl.loc.mod_path != node.owner.loc.mod_path {
            continue ;} else {
            pos = create_range(item.decl.loc);    
            symbol = lspt.DocumentSymbol(
                name=key,
                kind=kind_map(item.decl),
                range=pos,
                selection_range=pos,
                children=[]
            );    
            symbols.append(symbol) ;
        }
    }
    
    for sub_tab in [i for i in node.kid if i.owner.loc.mod_path == node.owner.loc.mod_path] {
        sub_symbols = collect_symbols(sub_tab);    
        if isinstance(
            sub_tab.owner,
            (ast.IfStmt, ast.ElseStmt, ast.WhileStmt, ast.IterForStmt, ast.InForStmt)
        ) {
            symbols.extend(sub_symbols) ;} else {
            sub_pos = create_range(sub_tab.owner.loc);    
            symbol = lspt.DocumentSymbol(
                name=sub_tab.name,
                kind=kind_map(sub_tab.owner),
                range=sub_pos,
                selection_range=sub_pos,
                children=sub_symbols
            );    
            symbols.append(symbol) ;
        }
    }
    
    return symbols ;
}

can owner_sym(table: SymbolTable) -> Optional[Symbol] {
    """Get owner sym.""" ;    
    if table.parent
        and isinstance(table.owner, ast.AstSymbolNode) {
        return table.parent.lookup(table.owner.sym_name) ;}
    
    return None ;
}

can create_range(loc: CodeLocInfo) -> lspt.Range {
    """Create an lspt.Range from a location object.""" ;    
    return lspt.Range(
        start=lspt.Position(
            line=(loc.first_line - 1) if loc.first_line > 0 else 0,
            character=(loc.col_start - 1) if loc.col_start > 0 else 0
        ),
        end=lspt.Position(
            line=(loc.last_line - 1) if loc.last_line > 0 else 0,
            character=(loc.col_end - 1) if loc.col_end > 0 else 0
        )
    ) ;
}

can kind_map(sub_tab: ast.AstNode) -> lspt.SymbolKind {
    """Map the symbol node to an lspt.SymbolKind.""" ;    
    return lspt.SymbolKind.Function if isinstance(sub_tab, (ast.Ability, ast.AbilityDef)) else lspt.SymbolKind.Class if isinstance(sub_tab, (ast.Architype, ast.ArchDef)) else lspt.SymbolKind.Module if isinstance(sub_tab, ast.Module) else lspt.SymbolKind.Enum if isinstance(sub_tab, (ast.Enum, ast.EnumDef)) else lspt.SymbolKind.Variable ;
}

can label_map(sub_tab: SymbolType) -> lspt.CompletionItemKind {
    """Map the symbol node to an lspt.CompletionItemKind.""" ;    
    return lspt.CompletionItemKind.Function if sub_tab in [SymbolType.ABILITY, SymbolType.TEST] else lspt.CompletionItemKind.Class if sub_tab in [
        SymbolType.OBJECT_ARCH,
        SymbolType.NODE_ARCH,
        SymbolType.EDGE_ARCH,
        SymbolType.WALKER_ARCH
    ] else lspt.CompletionItemKind.Module if sub_tab == SymbolType.MODULE else lspt.CompletionItemKind.Enum if sub_tab == SymbolType.ENUM_ARCH else lspt.CompletionItemKind.Field if sub_tab == SymbolType.HAS_VAR else lspt.CompletionItemKind.Method if sub_tab == SymbolType.METHOD else lspt.CompletionItemKind.EnumMember if sub_tab == SymbolType.ENUM_MEMBER else lspt.CompletionItemKind.Interface if sub_tab == SymbolType.IMPL else lspt.CompletionItemKind.Variable ;
}

can get_mod_path(mod_path: ast.ModulePath, name_node: ast.Name) -> (str | None) {
    """Get path for a module import name.""" ;    
    ret_target = None;    
    module_location_path = mod_path.loc.mod_path;    
    if mod_path.parent
        and isinstance(mod_path.parent.parent, ast.Import)
        and mod_path.parent.parent.hint.tag.value == "py"
        or isinstance(mod_path.parent, ast.Import)
        and mod_path.parent.from_loc
        and mod_path.parent.hint.tag.value == "py" {
        if mod_path.path and name_node in mod_path.path {
            temporary_path_str = (("." * mod_path.level) + ".".join(
                [p.value for p in mod_path.path[:(mod_path.path.index(name_node) + 1)]] if mod_path.path else ""
            ));} else {
            temporary_path_str = mod_path.path_str;
        }
        
        sys.path.append(os.path.dirname(module_location_path)) ;    
        spec = importlib.util.find_spec(temporary_path_str);    
        sys.path.remove(os.path.dirname(module_location_path)) ;    
        if spec
            and spec.origin
            and spec.origin.endswith(".py") {
            ret_target = spec.origin;}
    } elif mod_path.parent
        and isinstance(mod_path.parent.parent, ast.Import)
        and mod_path.parent.parent.hint.tag.value == "jac"
        or isinstance(mod_path.parent, ast.Import)
        and mod_path.parent.from_loc
        and mod_path.parent.hint.tag.value == "jac" {
        ret_target = import_target_to_relative_path(
            level=mod_path.level,
            target=mod_path.path_str,
            base_path=os.path.dirname(module_location_path)
        );}
    
    return ret_target ;
}

can get_item_path(mod_item: ast.ModuleItem) -> (tuple[(str, tuple[(int, int)])] | None) {
    """Get path.""" ;    
    item_name = mod_item.name.value;    
    if mod_item.from_parent.hint.tag.value == "py"
        and mod_item.from_parent.from_loc {
        path = get_mod_path(
            mod_item.from_parent.from_loc,
            mod_item.name
        );    
        if path {
            return get_definition_range(path, item_name) ;}
    } elif mod_item.from_parent.hint.tag.value == "jac" {
        mod_node = mod_item.from_mod_path;    
        if mod_node.sub_module
            and mod_node.sub_module._sym_tab {
            for (symbol_name, symbol) in mod_node.sub_module._sym_tab.tab.items() {
                if symbol_name == item_name {
                    return (symbol.decl.loc.mod_path, ((symbol.decl.loc.first_line - 1), (symbol.decl.loc.last_line - 1))) ;}
            }
        }
    }
    
    return None ;
}

can get_definition_range(filename: str, name: str) -> (tuple[(str, tuple[(int, int)])] | None) {
    """Get the start and end line of a function or class definition in a file.""" ;    
    import:py ast ;    
    with open(filename, "r") as file {
        source = file.read();
    }
    
    tree = ast.parse(source);    
    for node in ast.walk(tree) {
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
            and node.name == name {
            start_line = node.lineno;    
            end_line = node.body[-1].end_lineno if hasattr(node.body[-1], "end_lineno") else node.body[-1].lineno;    
            if start_line and end_line {
                return (filename, ((start_line - 1), (end_line - 1))) ;}
        } elif isinstance(node, ast.Assign) {
            for target in node.targets {
                if isinstance(target, ast.Name)
                    and target.id == name {
                    start_line = node.lineno;    
                    end_line = node.end_lineno if hasattr(node, "end_lineno") else node.lineno;    
                    if start_line and end_line {
                        return (filename, ((start_line - 1), (end_line - 1))) ;}
                }
            }
        }
    }
    
    return None ;
}

can collect_all_symbols_in_scope(sym_tab: SymbolTable, up_tree: bool=True) -> list[lspt.CompletionItem] {
    """Return all symbols in scope.""" ;    
    symbols = [];    
    visited = set();    
    current_tab: Optional[SymbolTable] = sym_tab;    
    
    while current_tab is not None
        and current_tab not in visited {
        visited.add(current_tab) ;    
        for (name, symbol) in current_tab.tab.items() {
            if name not in dir(builtins) {
                symbols.append(
                    lspt.CompletionItem(
                        label=name,
                        kind=label_map(symbol.sym_type)
                    )
                ) ;}
        }
        
        if not up_tree {
            return symbols ;}
        
        current_tab = current_tab.parent if current_tab.parent != current_tab else None;
    }
    
    return symbols ;
}

can parse_symbol_path(text: str, dot_position: int) -> list[str] {
    """Parse text and return a list of symbols.""" ;    
    text = text[:dot_position].strip();    
    pattern = re.compile("\\b\\w+\\(\\)?|\\b\\w+\\b");    
    matches = pattern.findall(text);    
    if text.endswith(".") {
        matches.append("") ;}
    
    symbol_path = [];    
    i = 0;    
    
    while i < len(matches) {
        if matches[i].endswith("(") {
            i += 1;    
            continue ;} elif "(" in matches[i] {
            symbol_path.append(matches[i]) ;} elif matches[i] == "" {;} else {
            symbol_path.append(matches[i]) ;
        }
        
        i += 1;
    }
    
    return symbol_path ;
}

can resolve_symbol_path(sym_name: str, node_tab: SymbolTable) -> str {
    """Resolve symbol path.""" ;    
    visited = set();    
    current_tab: Optional[SymbolTable] = node_tab;    
    
    while current_tab is not None
        and current_tab not in visited {
        visited.add(current_tab) ;    
        for (name, symbol) in current_tab.tab.items() {
            if name not in dir(builtins)
                and name == sym_name {
                path = symbol.defn[0]._sym_type;    
                return path ;}
        }
        
        current_tab = current_tab.parent if current_tab.parent != current_tab else None;
    }
    
    return "" ;
}

can find_symbol_table(path: str, current_tab: Optional[SymbolTable]) -> SymbolTable {
    """Find symbol table.""" ;    
    path = path.lstrip(".");    
    current_table = current_tab;    
    if current_table {
        for segment in path.split(".") {
            current_table = next(
                (child_table  for child_table in current_table.kid if child_table.name == segment),
                current_table
            );
        }
    }
    
    if current_table {
        return current_table ;}
    
    raise ValueError(f"{"Symbol table not found for path "}{path}") ;
}

can resolve_completion_symbol_table(mod_tab: SymbolTable, current_symbol_path: list[str], current_tab: Optional[SymbolTable]) -> list[lspt.CompletionItem] {
    """Resolve symbol table for completion items.""" ;    
    current_symbol_table = mod_tab;    
    for obj in current_symbol_path {
        if obj == "self" {
            
            try  {
                
                try  {
                    is_abilitydef = mod_tab.owner if isinstance(mod_tab.owner, ast.AbilityDef) else mod_tab.owner.parent_of_type(ast.AbilityDef);    
                    archi_owner = is_abilitydef.decl_link.parent_of_type(ast.Architype) if is_abilitydef.decl_link else None;    
                    current_symbol_table = archi_owner._sym_tab if archi_owner and archi_owner._sym_tab else mod_tab;    
                    continue ;} except ValueError {;
                }
                
                archi_owner = mod_tab.owner.parent_of_type(ast.Architype);    
                current_symbol_table = archi_owner._sym_tab if archi_owner and archi_owner._sym_tab else mod_tab;} except ValueError {;
            }
        } else {
            path: str = resolve_symbol_path(obj, current_symbol_table);    
            if path {
                current_symbol_table = find_symbol_table(path, current_tab);} elif isinstance(current_symbol_table.owner, ast.Architype)
                and current_symbol_table.owner.base_classes {
                for base_name in current_symbol_table.owner.base_classes.items {
                    if isinstance(base_name, ast.Name)
                        and base_name.sym {
                        path = ((base_name.sym.sym_dotted_name + ".") + obj);    
                        current_symbol_table = find_symbol_table(path, current_tab);}
                }
            }
        }
    }
    
    if isinstance(current_symbol_table.owner, ast.Architype)
        and current_symbol_table.owner.base_classes {
        base = [];    
        for base_name in current_symbol_table.owner.base_classes.items {
            if isinstance(base_name, ast.Name)
                and base_name.sym {
                base.append(base_name.sym.sym_dotted_name) ;}
        }
        
        for base_ in base {
            completion_items = collect_all_symbols_in_scope(
                find_symbol_table(base_, current_tab),
                up_tree=False
            );
        }
    } else {
        completion_items = [];
    }
    
    completion_items.extend(
        collect_all_symbols_in_scope(
            current_symbol_table,
            up_tree=False
        )
    ) ;    
    return completion_items ;
}

