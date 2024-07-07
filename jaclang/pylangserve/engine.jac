"""Living Workspace of Jac project."""

import:py from __future__, annotations ;
import:py asyncio ;
import:py logging ;
import:py from concurrent.futures, ThreadPoolExecutor ;
import:py from enum, IntEnum ;
import:py from typing, Optional ;
import:py jaclang.compiler.absyntree as ast ;
import:py from jaclang.compiler.compile, jac_ir_to_pass, jac_str_to_pass ;
import:py from jaclang.compiler.parser, JacParser ;
import:py from jaclang.compiler.passes, Pass ;
import:py from jaclang.compiler.passes.main.schedules, type_checker_sched ;
import:py from jaclang.compiler.passes.tool, FuseCommentsPass, JacFormatPass ;
import:py from jaclang.compiler.passes.transform, Alert ;
import:py from jaclang.langserve.utils, collect_all_symbols_in_scope, collect_symbols, create_range, find_deepest_symbol_node_at_pos, get_item_path, get_mod_path, parse_symbol_path, resolve_completion_symbol_table ;
import:py from jaclang.vendor.pygls, uris ;
import:py from jaclang.vendor.pygls.server, LanguageServer ;
import:py lsprotocol.types as lspt ;

"""Analysis Level successfully completed."""
class ALev : IntEnum : {
    with entry {
        QUICK = 1;    
        DEEP = 2;    
        TYPE = 3;
    }
}

"""Module IR and Stats."""
class ModuleInfo {
    can init(ir: ast.Module, errors: list[Alert], warnings: list[Alert], alev: ALev, parent: Optional[ModuleInfo]=None) -> None {
        """Initialize module info.""" ;    
        self.ir = ir;    
        self.errors = errors;    
        self.warnings = warnings;    
        self.alev = alev;    
        self.parent: Optional[ModuleInfo] = parent;    
        self.diagnostics = self.gen_diagnostics();    
        self.sem_tokens: list[int] = self.gen_sem_tokens();
    }
    
    @ property 
     can uri() -> str {
        """Return uri.""" ;    
        return uris.from_fs_path(self.ir.loc.mod_path) ;
    }
    
    can update_with(build: Pass, alev: ALev, refresh: bool=False, mod_override: Optional[ast.Module]=None) -> None {
        """Update module info.""" ;    
        target_mod = mod_override if mod_override else build.ir;    
        if not isinstance(target_mod, ast.Module) {
            return ;}
        
        self.ir = target_mod if alev > ALev.QUICK else self.ir;    
        if refresh {
            self.errors = build.errors_had;    
            self.warnings = build.warnings_had;} else {
            self.errors += [i for i in build.errors_had if i not in self.errors if i.loc.mod_path == target_mod.loc.mod_path];    
            self.warnings += [i for i in build.warnings_had if i not in self.warnings if i.loc.mod_path == target_mod.loc.mod_path];
        }
        
        self.alev = alev;    
        self.diagnostics = self.gen_diagnostics();    
        if self.alev == ALev.TYPE {
            self.sem_tokens = self.gen_sem_tokens();}
    }
    
    can gen_diagnostics() -> list[lspt.Diagnostic] {
        """Return diagnostics.""" ;    
        return ([lspt.Diagnostic(
            range=create_range(error.loc),
            message=error.msg,
            severity=lspt.DiagnosticSeverity.Error
        ) for error in self.errors] + [lspt.Diagnostic(
            range=create_range(warning.loc),
            message=warning.msg,
            severity=lspt.DiagnosticSeverity.Warning
        ) for warning in self.warnings]) ;
    }
    
    can gen_sem_tokens() -> list[int] {
        """Return semantic tokens.""" ;    
        tokens = [];    
        (prev_line, prev_col) = (0, 0);    
        for node in self.ir._in_mod_nodes {
            if isinstance(node, ast.NameAtom)
                and node.sem_token {
                (line, col_start, col_end) = ((node.loc.first_line - 1), (node.loc.col_start - 1), (node.loc.col_end - 1));    
                length = (col_end - col_start);    
                tokens += [
                    (line - prev_line),
                    col_start if line != prev_line else (col_start - prev_col),
                    length,
                    *node.sem_token
                ];    
                (prev_line, prev_col) = (line, col_start);}
        }
        
        return tokens ;
    }
}

"""Class for managing workspace."""
class JacLangServer : LanguageServer : {
    can init() -> None {
        """Initialize workspace.""" ;    
        super.init("jac-lsp", "v0.1") ;    
        self.modules: dict[(str, ModuleInfo)] = {};    
        self.executor = ThreadPoolExecutor();
    }
    
    async can push_diagnostics(file_path: str) -> None {
        """Push diagnostics for a file.""" ;    
        if file_path in self.modules {
            self.publish_diagnostics(
                file_path,
                self.modules[file_path].diagnostics
            ) ;}
    }
    
    can unwind_to_parent(file_path: str) -> str {
        """Unwind to parent.""" ;    
        orig_file_path = file_path;    
        if file_path in self.modules {
            while cur := self.modules[file_path].parent {
                file_path = cur.uri;
            }
            
            if file_path == orig_file_path
                and discover := self.modules[file_path].ir.annexable_by {
                file_path = uris.from_fs_path(discover);    
                self.quick_check(file_path) ;}
        }
        
        return file_path ;
    }
    
    can update_modules(file_path: str, build: Pass, alev: ALev, refresh: bool=False) -> None {
        """Update modules.""" ;    
        if not isinstance(build.ir, ast.Module) {
            self.log_error("Error with module build.") ;    
            return ;}
        
        if file_path in self.modules {
            self.modules[file_path].update_with(
                build,
                alev,
                refresh=refresh
            ) ;} else {
            self.modules[file_path] = ModuleInfo(
                ir=build.ir,
                errors=[i for i in build.errors_had if i.loc.mod_path == uris.to_fs_path(file_path)],
                warnings=[i for i in build.warnings_had if i.loc.mod_path == uris.to_fs_path(file_path)],
                alev=alev
            );
        }
        
        for p in build.ir.mod_deps.keys() {
            uri = uris.from_fs_path(p);    
            if not refresh and uri in self.modules {
                self.modules[uri].update_with(
                    build,
                    alev,
                    mod_override=build.ir.mod_deps[p],
                    refresh=refresh
                ) ;} else {
                self.modules[uri] = ModuleInfo(
                    ir=build.ir.mod_deps[p],
                    errors=[i for i in build.errors_had if i.loc.mod_path == p],
                    warnings=[i for i in build.warnings_had if i.loc.mod_path == p],
                    alev=alev
                );
            }
            
            self.modules[uri].parent = self.modules[file_path] if file_path != uri else None;
        }
    }
    
    can quick_check(file_path: str) -> bool {
        """Rebuild a file.""" ;    
        try  {
            document = self.workspace.get_text_document(file_path);    
            build = jac_str_to_pass(
                jac_str=document.source,
                file_path=document.path,
                schedule=[]
            );} except Exception as e {
            self.log_error(f"{"Error during syntax check: "}{e}") ;    
            return False ;
        }
        
        self.update_modules(
            file_path,
            build,
            ALev.QUICK,
            refresh=True
        ) ;    
        return len(self.modules[file_path].errors) == 0 ;
    }
    
    can deep_check(file_path: str) -> bool {
        """Rebuild a file and its dependencies.""" ;    
        if file_path not in self.modules {
            self.quick_check(file_path) ;}
        
        try  {
            file_path = self.unwind_to_parent(file_path);    
            build = jac_ir_to_pass(ir=self.modules[file_path].ir);} except Exception as e {
            self.log_error(f"{"Error during syntax check: "}{e}") ;    
            return False ;
        }
        
        self.update_modules(file_path, build, ALev.DEEP) ;    
        return len(self.modules[file_path].errors) == 0 ;
    }
    
    can type_check(file_path: str) -> bool {
        """Rebuild a file and its dependencies.""" ;    
        if file_path not in self.modules {
            self.deep_check(file_path) ;}
        
        try  {
            file_path = self.unwind_to_parent(file_path);    
            build = jac_ir_to_pass(
                ir=self.modules[file_path].ir,
                schedule=type_checker_sched
            );} except Exception as e {
            self.log_error(f"{"Error during type check: "}{e}") ;    
            return False ;
        }
        
        self.update_modules(file_path, build, ALev.TYPE) ;    
        return len(self.modules[file_path].errors) == 0 ;
    }
    
    async can analyze_and_publish(uri: str, level: int=2) -> None {
        """Analyze and publish diagnostics.""" ;    
        self.log_py(f"{"Analyzing "}{uri}{"..."}") ;    
        success = awaitasyncio.get_event_loop().run_in_executor(
            self.executor,
            self.quick_check,
            uri
        );    
        awaitself.push_diagnostics(uri) ;    
        if success and level > 0 {
            success = awaitasyncio.get_event_loop().run_in_executor(
                self.executor,
                self.deep_check,
                uri
            );    
            awaitself.push_diagnostics(uri) ;    
            if level > 1 {
                awaitasyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self.type_check,
                    uri
                ) ;    
                awaitself.push_diagnostics(uri) ;}
        }
    }
    
    can get_completion(file_path: str, position: lspt.Position, completion_trigger: str) -> lspt.CompletionList {
        """Return completion for a file.""" ;    
        completion_items = [];    
        document = self.workspace.get_text_document(file_path);    
        current_line = document.lines[position.line];    
        current_pos = position.character;    
        current_symbol_path = parse_symbol_path(current_line, current_pos);    
        node_selected = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir,
            position.line,
            (position.character - 2)
        );    
        mod_tab = self.modules[file_path].ir.sym_tab if not node_selected else node_selected.sym_tab;    
        current_tab = self.modules[file_path].ir._sym_tab;    
        current_symbol_table = mod_tab;    
        if completion_trigger == "." {
            completion_items = resolve_completion_symbol_table(
                mod_tab,
                current_symbol_path,
                current_tab
            );} else {
            
            try  {
                completion_items = collect_all_symbols_in_scope(current_symbol_table);} except AttributeError {;
            }
        }
        
        return lspt.CompletionList(
            is_incomplete=False,
            items=completion_items
        ) ;
    }
    
    can rename_module(old_path: str, new_path: str) -> None {
        """Rename module.""" ;    
        if old_path in self.modules
            and new_path != old_path {
            self.modules[new_path] = self.modules[old_path];    
            del (self.modules[old_path]
            ,) ;}
    }
    
    can delete_module(uri: str) -> None {
        """Delete module.""" ;    
        if uri in self.modules {
            del (self.modules[uri]
            ,) ;}
    }
    
    can formatted_jac(file_path: str) -> list[lspt.TextEdit] {
        """Return formatted jac.""" ;    
        try  {
            document = self.workspace.get_text_document(file_path);    
            format = jac_str_to_pass(
                jac_str=document.source,
                file_path=document.path,
                target=JacFormatPass,
                schedule=[FuseCommentsPass, JacFormatPass]
            );    
            formatted_text = format.ir.gen.jac if JacParser not in [e.from_pass for e in format.errors_had] else document.source;} except Exception as e {
            self.log_error(f"{"Error during formatting: "}{e}") ;    
            formatted_text = document.source;
        }
        
        return [
            lspt.TextEdit(
                range=lspt.Range(
                    start=lspt.Position(line=0, character=0),
                    end=lspt.Position(
                        line=(len(document.source.splitlines()) + 1),
                        character=0
                    )
                ),
                new_text=formatted_text
            )
        ] ;
    }
    
    can get_hover_info(file_path: str, position: lspt.Position) -> Optional[lspt.Hover] {
        """Return hover information for a file.""" ;    
        node_selected = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir,
            position.line,
            position.character
        );    
        value = self.get_node_info(node_selected) if node_selected else None;    
        if value {
            return lspt.Hover(
                contents=lspt.MarkupContent(
                    kind=lspt.MarkupKind.PlainText,
                    value=f"{value}"
                )
            ) ;}
        
        return None ;
    }
    
    can get_node_info(node: ast.AstSymbolNode) -> Optional[str] {
        """Extract meaningful information from the AST node.""" ;    
        try  {
            if isinstance(node, ast.NameAtom) {
                node = node.name_of;}
            
            access = (node.sym.access.value + " ") if node.sym else None;    
            node_info = f"{"("}{access if access else ""}{node.sym_category.value}{") "}{node.sym_name}";    
            if node.name_spec.clean_type {
                node_info += f"{": "}{node.name_spec.clean_type}";}
            
            if isinstance(node, ast.AstSemStrNode)
                and node.semstr {
                node_info += f"{"\n"}{node.semstr.value}";}
            
            if isinstance(node, ast.AstDocNode)
                and node.doc {
                node_info += f"{"\n"}{node.doc.value}";}
            
            if isinstance(node, ast.Ability)
                and node.signature {
                node_info += f"{"\n"}{node.signature.unparse()}";}
            
            self.log_py(f"{"mypy_node: "}{node.gen.mypy_ast}") ;} except AttributeError as e {
            self.log_warning(
                f"{"Attribute error when accessing node attributes: "}{e}"
            ) ;
        }
        
        return node_info.strip() ;
    }
    
    can get_document_symbols(file_path: str) -> list[lspt.DocumentSymbol] {
        """Return document symbols for a file.""" ;    
        if file_path in self.modules
            and root_node := self.modules[file_path].ir._sym_tab {
            return collect_symbols(root_node) ;}
        
        return [] ;
    }
    
    can get_definition(file_path: str, position: lspt.Position) -> Optional[lspt.Location] {
        """Return definition location for a file.""" ;    
        node_selected: Optional[ast.AstSymbolNode] = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir,
            position.line,
            position.character
        );    
        if node_selected {
            if isinstance(node_selected, ast.Name)
                and node_selected.parent
                and isinstance(node_selected.parent, ast.ModulePath) {
                spec = get_mod_path(node_selected.parent, node_selected);    
                if spec {
                    return lspt.Location(
                        uri=uris.from_fs_path(spec),
                        range=lspt.Range(
                            start=lspt.Position(line=0, character=0),
                            end=lspt.Position(line=0, character=0)
                        )
                    ) ;} else {
                    return None ;
                }
            } elif node_selected.parent
                and isinstance(node_selected.parent, ast.ModuleItem) {
                path_range = get_item_path(node_selected.parent);    
                if path_range {
                    (path, range) = path_range;    
                    if path and range {
                        return lspt.Location(
                            uri=uris.from_fs_path(path),
                            range=lspt.Range(
                                start=lspt.Position(line=range[0], character=0),
                                end=lspt.Position(line=range[1], character=5)
                            )
                        ) ;}
                } else {
                    return None ;
                }
            } elif isinstance(
                node_selected,
                (ast.ElementStmt, ast.BuiltinType)
            ) {
                return None ;}
            
            decl_node = node_selected.parent.body.target if node_selected.parent
                and isinstance(node_selected.parent, ast.AstImplNeedingNode)
                and isinstance(
                node_selected.parent.body,
                ast.AstImplOnlyNode
            ) else node_selected.sym.decl if node_selected.sym and node_selected.sym.decl else node_selected;    
            self.log_py(f"{node_selected}{", "}{decl_node}") ;    
            decl_uri = uris.from_fs_path(decl_node.loc.mod_path);    
            
            try  {
                decl_range = create_range(decl_node.loc);} except ValueError {
                return None ;
            }
            
            decl_location = lspt.Location(uri=decl_uri, range=decl_range);    
            return decl_location ;} else {
            return None ;
        }
    }
    
    can get_references(file_path: str, position: lspt.Position) -> list[lspt.Location] {
        """Return references for a file.""" ;    
        node_selected = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir,
            position.line,
            position.character
        );    
        if node_selected and node_selected.sym {
            list_of_references: list[lspt.Location] = [lspt.Location(
                uri=uris.from_fs_path(node.loc.mod_path),
                range=create_range(node.loc)
            ) for node in node_selected.sym.uses];    
            return list_of_references ;}
        
        return [] ;
    }
    
    can get_semantic_tokens(file_path: str) -> lspt.SemanticTokens {
        """Return semantic tokens for a file.""" ;    
        if file_path not in self.modules {
            return lspt.SemanticTokens(data=[]) ;}
        
        return lspt.SemanticTokens(
            data=self.modules[file_path].sem_tokens
        ) ;
    }
    
    can log_error(message: str) -> None {
        """Log an error message.""" ;    
        self.show_message_log(message, lspt.MessageType.Error) ;    
        self.show_message(message, lspt.MessageType.Error) ;
    }
    
    can log_warning(message: str) -> None {
        """Log a warning message.""" ;    
        self.show_message_log(message, lspt.MessageType.Warning) ;    
        self.show_message(message, lspt.MessageType.Warning) ;
    }
    
    can log_info(message: str) -> None {
        """Log an info message.""" ;    
        self.show_message_log(message, lspt.MessageType.Info) ;    
        self.show_message(message, lspt.MessageType.Info) ;
    }
    
    can log_py(message: str) -> None {
        """Log a message.""" ;    
        logging.info(message) ;
    }
}

