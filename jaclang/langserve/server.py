"""Jaclang Language Server."""

from __future__ import annotations

import os
from typing import Any, Generator, Optional, Sequence

import jaclang.compiler.absyntree as ast
from jaclang.compiler.compile import jac_str_to_pass
from jaclang.compiler.passes.main import DefUsePass, schedules
from jaclang.compiler.passes.tool import FuseCommentsPass, JacFormatPass
from jaclang.compiler.passes.transform import Alert
from jaclang.compiler.symtable import Symbol, SymbolTable
from jaclang.langserve.utils import log, log_error
from jaclang.vendor.pygls.server import LanguageServer

import lsprotocol.types as lspt


def update_symbols(symtab: SymbolTable) -> Optional[list[Symbol]]:
    """Update symbols."""
    symbols = []

    def all_symbols(symtab: SymbolTable) -> Optional[list[Symbol]]:
        """Get all symbols in the symbol table."""
        for _, v in symtab.tab.items():
            symbols.append(v)
        for i in symtab.kid:
            all_symbols(i)
        return symbols

    return all_symbols(symtab)


class ModuleInfo:
    """Module IR and Stats."""

    def __init__(
        self,
        ir: Optional[ast.Module],
        errors: Sequence[Alert],
        warnings: Sequence[Alert],
        symbols: Optional[list[Symbol]] = None,
    ) -> None:
        """Initialize module info."""
        self.ir = ir
        self.errors = errors
        self.warnings = warnings
        self.symbols = symbols


class JacAnalyzer(LanguageServer):
    """Class for managing workspace."""

    def __init__(self) -> None:
        """Initialize workspace."""
        super().__init__("jac-lsp", "v0.1")
        self.path = r"C:/Users/PavinithanRetnakumar/OneDrive - BCS TECHNOLOGY INTERNATIONAL PTY LIMITED/Desktop/JAC/jaclang/"  # fix me
        self.modules: dict[str, ModuleInfo] = {}
        self.rebuild_workspace()

    def rebuild_workspace(self) -> None:
        """Rebuild workspace."""
        x = 1
        self.modules = {}
        for file in [
            os.path.normpath(os.path.join(root, name))
            for root, _, files in os.walk(self.path)
            for name in files
            if name.endswith(".jac")
        ]:
            # avoid building all files [for the hover ,now we are building only 1 file(guess_game_3.jac)]
            if x == 2:
                return
            x += 1
            type_check = False
            # lazy_parse = False
            # if file in self.modules:
            #     continue
            # if lazy_parse:
            #     # If lazy_parse is True, add the file to modules with empty IR
            #     self.modules[file] = ModuleInfo(
            #         ir=None,
            #         errors=[],
            #         warnings=[],
            #     )
            #     continue

            with open(file, "r") as f:
                source = f.read()
            build = jac_str_to_pass(
                jac_str=source,
                file_path=file,
                schedule=(
                    schedules.py_code_gen_typed if type_check else schedules.py_code_gen
                ),
                target=DefUsePass if not type_check else None,
            )
            # if not isinstance(build.ir, ast.Module):
            #     src = ast.JacSource(source, mod_path=file)
            #     self.modules[file] = ModuleInfo(
            #         ir=ast.Module(
            #             name="",
            #             doc=None,
            #             body=[],
            #             source=src,
            #             is_imported=False,
            #             kid=[src],
            #         ),
            #         errors=build.errors_had,
            #         warnings=build.warnings_had,
            #     )
            #     continue
            self.modules[file] = ModuleInfo(
                ir=build.ir,
                errors=build.errors_had,
                warnings=build.warnings_had,
            )
            self.modules[file].symbols = update_symbols(build.ir.sym_tab)
            log(f"symbols are  {self.modules[file].symbols[-13:]}")
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
        log(f"errors: {result.errors_had}")
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
    log(f"document. uri {params.text_document.uri}")
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
def hover(ls: JacAnalyzer, params: lspt.TextDocumentPositionParams) -> None:
    """Provide hover information for the given hover request."""
    log(f"position: {params}")
    log(list(server.modules.values())[0])

    def get_value() -> Optional[str]:
        """Get value by using the position to get which AST node it falls under."""
        line = params.position.line
        character = params.position.character

        def position_within_node(node: ast.AstNode, line: int, character: int) -> bool:
            """Check if the position falls within the node's location."""
            if node.loc.first_line < line + 1 < node.loc.last_line:
                return True
            if (
                node.loc.first_line == line + 1
                and node.loc.col_start <= character
                and (
                    node.loc.last_line == line + 1
                    and node.loc.col_end >= character
                    or node.loc.last_line > line + 1
                )
            ):
                return True
            if (
                node.loc.last_line == line + 1
                and node.loc.col_start <= character <= node.loc.col_end
            ):
                return True
            return False

        def find_deepest_node(
            node: ast.AstNode, line: int, character: int
        ) -> Generator[Any, Any, Any]:
            """Find the deepest node that contains the given position."""
            if position_within_node(node, line, character):
                yield node
                for child in node.kid:
                    yield from find_deepest_node(child, line, character)

        root_node = list(server.modules.values())[0].ir
        deepest_node = None
        for node in find_deepest_node(root_node, line, character):
            deepest_node = node

        def get_node_info(node: ast.AstNode) -> str:
            """Extract meaningful information from the AST node."""
            node_info = f"Node type: {type(node).__name__}\n"
            try:
                if not isinstance(node, ast.AstSymbolNode):
                    if hasattr(node, "name"):
                        node_info += f"Name: {node.name}\n"
                    if hasattr(node, "value"):
                        node_info += f"Value: {node.value}\n"
                    if hasattr(node, "loc"):
                        node_info += f"Location: ({node.loc.first_line}:{node.loc.col_start} - \
                                        {node.loc.last_line}:{node.loc.col_end})\n"
                else:
                    log(f"symlink node {node.sym_link}")
                    log(f"sym info  {node.sym_info}")
                    if node.sym_link and node.sym_link.decl:
                        decl_node = node.sym_link.decl
                        if isinstance(decl_node, ast.Architype):
                            node_info = (
                                f"(object) {node.value} \n{decl_node.doc.lit_value}"
                            )
                        elif isinstance(node.sym_link.decl, ast.Ability):
                            log("comeshere")
                            if node.sym_link.decl.doc:
                                node_info = f"(ability) {node.value} \n{node.sym_link.decl.doc.lit_value}"
                            else:
                                node_info = f"(ability) {node.value}"
                        elif isinstance(decl_node, ast.Name):
                            if (
                                decl_node.parent
                                and isinstance(decl_node.parent, ast.SubNodeList)
                                and decl_node.parent.parent
                                and isinstance(decl_node.parent.parent, ast.Assignment)
                            ):
                                node_info = f"(variable) {node.value}: \
                                    {node.sym_link.decl.parent.parent.value.unparse()}"
                            else:
                                node_info = (
                                    f"(name) {node.value} \n{node.sym_link.decl}"
                                )
                    else:
                        node_info += f"Name: {node.sym_link.sym_name}\n"

            except AttributeError as e:
                log(f"Attribute error when accessing node attributes: {e}")
            return node_info.strip()

        if deepest_node:
            return get_node_info(deepest_node)
        return None

    value = get_value()
    if value:
        return lspt.Hover(
            contents=lspt.MarkupContent(
                kind=lspt.MarkupKind.PlainText, value=f"{value}"
            ),
        )
    return None


def run_lang_server() -> None:
    """Run the language server."""
    server.start_io()
