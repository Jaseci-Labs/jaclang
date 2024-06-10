"""Jaclang Language Server."""
from __future__ import annotations
import os
from typing import Optional, Sequence
import jaclang.compiler.absyntree as ast
from jaclang.compiler.passes.main import DefUsePass, schedules

from jaclang.compiler.compile import jac_str_to_pass
from jaclang.compiler.passes.tool import FuseCommentsPass, JacFormatPass
from jaclang.langserve.utils import log, log_error
from jaclang.vendor.pygls.server import LanguageServer
from jaclang.compiler.passes.transform import Alert
from jaclang.compiler.symtable import SymbolTable,Symbol
from typing import Optional

import lsprotocol.types as lspt


# class AstNode:
#     """Abstract syntax tree node for Jac."""

#     def __init__(self, kid: Sequence[AstNode]) -> None:
#         """Initialize ast."""
#         self.parent: Optional[AstNode] = None
#         self.kid: list[AstNode] = [x.set_parent(self) for x in kid]
#         self.sym_tab: Optional[SymbolTable] = None
#         self._sub_node_tab: dict[type, list[AstNode]] = {}
#         self._typ: type = type(None)
#         self.gen: CodeGenTarget = CodeGenTarget()
#         self.meta: dict[str, str] = {}
#         self.loc: CodeLocInfo = CodeLocInfo(*self.resolve_tok_range())


# class CodeLocInfo:
#     """Code location info."""

#     def __init__(
#         self,
#         first_tok: Token,
#         last_tok: Token,
#     ) -> None:
#         """Initialize code location info."""
#         self.first_tok = first_tok
#         self.last_tok = last_tok

#     @property
#     def mod_path(self) -> str:
#         """Get line number."""
#         return self.first_tok.file_path

#     @property
#     def first_line(self) -> int:
#         """Get line number."""
#         return self.first_tok.line_no

#     @property
#     def last_line(self) -> int:
#         """Get line number."""
#         return self.last_tok.line_no

#     @property
#     def col_start(self) -> int:
#         """Get column position number."""
#         return self.first_tok.c_start

#     @property
#     def col_end(self) -> int:
#         """Get column position number."""
#         return self.last_tok.c_end

#     @property
#     def pos_start(self) -> int:
#         """Get column position number."""
#         return self.first_tok.pos_start

#     @property
#     def pos_end(self) -> int:
#         """Get column position number."""
#         return self.last_tok.pos_end

#     @property
#     def tok_range(self) -> tuple[Token, Token]:
#         """Get token range."""
#         return (self.first_tok, self.last_tok)

#     @property
#     def first_token(self) -> Token:
#         """Get first token."""
#         return self.first_tok

#     @property
#     def last_token(self) -> Token:
#         """Get last token."""
#         return self.last_tok

#     def update_token_range(self, first_tok: Token, last_tok: Token) -> None:
#         """Update token range."""
#         self.first_tok = first_tok
#         self.last_tok = last_tok

#     def update_first_token(self, first_tok: Token) -> None:
#         """Update first token."""
#         self.first_tok = first_tok

#     def update_last_token(self, last_tok: Token) -> None:
#         """Update last token."""
#         self.last_tok = last_tok

#     def __str__(self) -> str:
#         """Stringify."""
#         return f"{self.first_tok.line_no}:{self.first_tok.c_start} - {self.last_tok.line_no}:{self.last_tok.c_end}"

# Symbols can have mulitple definitions but resolves decl to be the
# first such definition in a given scope.
# class Symbol:
#     """Symbol."""

#     def __init__(
#         self,
#         defn: ast.AstSymbolNode,
#         access: SymbolAccess,
#         parent_tab: SymbolTable,
#         typ: Optional[type] = None,
#     ) -> None:
#         """Initialize."""
#         self.typ = typ
#         self.defn: list[ast.AstSymbolNode] = [defn]
#         defn.sym_link = self
#         self.access = access
#         self.parent_tab = parent_tab

#     @property
#     def decl(self) -> ast.AstSymbolNode:
#         """Get decl."""
#         return self.defn[0]

#     @property
#     def sym_name(self) -> str:
#         """Get name."""
#         return self.decl.sym_name

#     @property
#     def sym_type(self) -> SymbolType:
#         """Get sym_type."""
#         return self.decl.sym_type

#     def add_defn(self, node: ast.AstSymbolNode) -> None:
#         """Add defn."""
#         self.defn.append(node)
#         node.sym_link = self

#     def __repr__(self) -> str:
#         """Repr."""
#         return (
#             f"Symbol({self.sym_name}, {self.sym_type}, {self.access}, "
#             f"{self.typ}, {self.defn})"
#         )
    

def update_symbols(symtab: SymbolTable) -> list:
    symbols=[]
    def all_symbols(symtab: SymbolTable) -> list:
        for k,v in symtab.tab.items():
            symbols.append(v)
        for i in symtab.kid:
            all_symbols(i)
        return symbols
    return all_symbols(symtab)


def get_symbol_node(posi: lspt.Position,symbols: list[Symbol]) -> Optional[Symbol]:
    # first lets find the decl and then from decl return the ast symbol node
    log(f'{symbols[0].parent_tab.owner}')
    # log(f'position: {posi.line} {posi.character}')
    # for sym in symbols:
    #     if sym.defn[0].loc.first_line==posi.line+1 and sym.defn[0].loc.col_start<=posi.character and sym.defn[0].loc.col_end>=posi.character:
    #         return sym


class ModuleInfo:
    """Module IR and Stats."""

    def __init__(
        self,
        ir: Optional[ast.Module],
        errors: Sequence[Alert],
        warnings: Sequence[Alert],
        symbols: Optional[Symbol] = [],
    ) -> None:
        """Initialize module info."""
        self.ir = ir
        self.errors = errors
        self.warnings = warnings
        self.symbols = symbols

class JacAnalyzer(LanguageServer):
    """Class for managing workspace."""

    def __init__(self):
        """Initialize workspace."""
        super().__init__("jac-lsp", "v0.1")
        self.path=r'/home/acer/Desktop/jac_kug/jaclang/'
        self.modules: dict[str, ModuleInfo] = {}
        self.rebuild_workspace()
    
    def rebuild_workspace(self) -> None:
        """Rebuild workspace."""
        log(f'working directory---> {self.path}')
        x=1
        self.modules = {}
        for file in [
            os.path.normpath(os.path.join(root, name))
            for root, _, files in os.walk(self.path)
            for name in files
            if name.endswith(".jac")
        ]:
            
            if 'ures/simple_persistent.jac' in str(file) or x==5:
                    return
            x+=1
            lazy_parse = False
            type_check = False
            log(f'file---> {file}')
            if file in self.modules:
                log(f'file already in modules---> {file}')
                continue
            if lazy_parse:
                # If lazy_parse is True, add the file to modules with empty IR
                self.modules[file] = ModuleInfo(
                    ir=None,
                    errors=[],
                    warnings=[],
                )
                continue

            with open(file, "r") as f:
                source = f.read()
            build = jac_str_to_pass(
                jac_str=source,
                file_path=file,
                schedule=(
                    schedules.py_code_gen_typed
                    if type_check
                    else schedules.py_code_gen
                ),
                target=DefUsePass if not type_check else None,
            )
            if not isinstance(build.ir, ast.Module):
                src = ast.JacSource(source, mod_path=file)
                self.modules[file] = ModuleInfo(
                    ir=ast.Module(
                        name="",
                        doc=None,
                        body=[],
                        source=src,
                        is_imported=False,
                        kid=[src],
                    ),
                    errors=build.errors_had,
                    warnings=build.warnings_had,
                )
                continue
            self.modules[file] = ModuleInfo(
                ir=build.ir,
                errors=build.errors_had,
                warnings=build.warnings_had,
            )
            log('all symbolss --')
            self.modules[file].symbols=update_symbols(build.ir.sym_tab)
            log(f'symbols are  {self.modules[file].symbols}')
            if build.ir:
                for sub in build.ir.mod_deps:
                    self.modules[sub] = ModuleInfo(
                        ir=build.ir.mod_deps[sub],
                        errors=build.errors_had,
                        warnings=build.warnings_had,
                    )        
            
server = JacAnalyzer()


@server.feature(lspt.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: JacAnalyzer, params: lspt.DidChangeTextDocumentParams) -> None:
    """Check syntax on change."""
    server.path = ls.workspace.root_path # this line should go at opening / initialization of workspace @marsninja
    document = ls.workspace.get_document(params.text_document.uri)
    try:
        result = jac_str_to_pass(
            jac_str=document.source,
            file_path=document.path,
            schedule=[],
        )
        server.modules[document.path] = ModuleInfo(
            ir=result.ir,
            errors=result.errors_had,
            warnings=result.warnings_had,
        )
        log(f'errors: {result.errors_had}')
        if not result.errors_had and not result.warnings_had:
            ls.publish_diagnostics(document.uri, [])
        else:
            ls.publish_diagnostics(
                document.uri,
                [
                    lspt.Diagnostic(
                        range=lspt.Range(
                            start=lspt.Position(
                                line=error.loc.first_line, character=error.loc.col_start
                            ),
                            end=lspt.Position(
                                line=error.loc.last_line,
                                character=error.loc.col_end,
                            ),
                        ),
                        message=error.msg,
                        severity=lspt.DiagnosticSeverity.Error,
                    )
                    for error in result.errors_had
                ],
            )
    except Exception as e:
        log_error(ls, f"Error during syntax check: {e}")
        log(f"Error during syntax check: {e}")


@server.feature(
    lspt.TEXT_DOCUMENT_COMPLETION,
    lspt.CompletionOptions(trigger_characters=[".", ":", ""]),
)
def completions(params: lspt.CompletionParams) -> None:
    """Provide completions for the given completion request."""
    items = []
    log(f'document. uri {params.text_document.uri}')
    document = server.workspace.get_text_document(params.text_document.uri)
    current_line = document.lines[params.position.line].strip()
    if current_line.endswith("hello."):

        items = [
            lspt.CompletionItem(label="world"),
            lspt.CompletionItem(label="friend"),
        ]
    return lspt.CompletionList(is_incomplete=False, items=items)


@server.feature(lspt.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: LanguageServer, params: lspt.DocumentFormattingParams
) -> list[lspt.TextEdit]:
    """Format the given document."""
    try:
        document = ls.workspace.get_document(params.text_document.uri)
        formatted_text = jac_str_to_pass(
            jac_str=document.source,
            file_path=document.path,
            target=JacFormatPass,
            schedule=[FuseCommentsPass, JacFormatPass],
        ).ir.gen.jac
    except Exception as e:
        log_error(ls, f"Error during formatting: {e}")
        formatted_text = document.source
    return [
        lspt.TextEdit(
            range=lspt.Range(
                start=lspt.Position(line=0, character=0),
                end=lspt.Position(line=len(formatted_text), character=0),
            ),
            new_text=formatted_text,
        )
    ]

@server.feature(lspt.TEXT_DOCUMENT_HOVER, lspt.HoverOptions(work_done_progress=True))
def hover(ls, params: lspt.HoverParams) -> Optional[lspt.Hover]:
    """Provide hover information for the given hover request."""
    # document = ls.workspace.get_document(params.text_document.uri)
    # current_line = document.lines[params.position.line].strip()
    # i need to print the position of the cursor
    log(f'params:--> {params.text_document.uri[7:]}' )
    # ir=server.modules[params.text_document.uri[7:]].ir
    # log(f'{server.}')
    # first key of server.modules is 
    log(f'first key of server.modules: {list(server.modules.values())[0]}')
    # log(f'first key of server.modules: {list(server.modules.values())[0].ir.sym_tab}')
    log(f'first key of server.modules: {list(server.modules.values())[0].ir.sym_tab.owner}')
    log(f'first key of server.modules: {list(server.modules.values())[0].ir.sym_tab.kid}')
    # log(f'first key of server.modules: {list(server.modules.values())[0].ir.sym_tab.tab}')
    # for sym in list(server.modules.values())[0].ir.sym_tab.tab:
    #     log(f'sym: {sym}')
    # log(f'first key of server.modules: {list(server.modules.values())[0].ir.sym_tab.uses}')
    # log(f'ir: {ir.pp()}')
    log(f'position: {params}')
    log(f'position ufff: {params.position}')
    log(f'position: {params.position.line}')
    log(f'position: {params.position.character}')
    # if current_line.endswith("hello."):
    log(list(server.modules.values())[0])
    # sym_node=get_symbol_node(params.position,list(server.modules.values())[0].symbols)
    # log(f'relevant sym_node: {sym_node}')
    return lspt.Hover(
        contents=lspt.MarkupContent(
            kind=lspt.MarkupKind.PlainText, value="Hello, world!"
        ),
        # range=lspt.Range(
        #     start=lspt.Position(line=params.position.line, character=0),
        #     end=lspt.Position(line=params.position.line, character=len(current_line)),
        # ),
    )
    return None

def run_lang_server() -> None:
    """Run the language server."""
    server.start_io()
