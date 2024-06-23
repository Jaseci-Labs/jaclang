"""Living Workspace of Jac project."""

from __future__ import annotations

import logging
from enum import IntEnum
from hashlib import md5
from typing import Optional


import jaclang.compiler.absyntree as ast
from jaclang.compiler.compile import jac_ir_to_pass, jac_str_to_pass
from jaclang.compiler.parser import JacParser
from jaclang.compiler.passes import Pass
from jaclang.compiler.passes.main.schedules import type_checker_sched
from jaclang.compiler.passes.tool import FuseCommentsPass, JacFormatPass
from jaclang.compiler.passes.transform import Alert
from jaclang.langserve.utils import (
    collect_symbols,
    create_range,
    find_deepest_symbol_node_at_pos,
)
from jaclang.vendor.pygls import uris
from jaclang.vendor.pygls.server import LanguageServer

import lsprotocol.types as lspt


class ALev(IntEnum):
    """Analysis Level."""

    QUICK = 1
    DEEP = 2
    TYPE = 3


class ModuleInfo:
    """Module IR and Stats."""

    def __init__(
        self,
        ir: ast.Module,
        errors: list[Alert],
        warnings: list[Alert],
        alev: ALev,
        parent: Optional[ModuleInfo] = None,
    ) -> None:
        """Initialize module info."""
        self.ir = ir
        self.errors = errors
        self.warnings = warnings
        self.alev = alev
        self.parent: Optional[ModuleInfo] = parent
        self.diagnostics = self.gen_diagnostics()

    @property
    def uri(self) -> str:
        """Return uri."""
        return uris.from_fs_path(self.ir.loc.mod_path)

    @property
    def has_syntax_error(self) -> bool:
        """Return if there are syntax errors."""
        return len(self.errors) > 0 and self.alev == ALev.QUICK

    def update_with(self, new_info: ModuleInfo) -> None:
        """Update module info."""
        self.ir = new_info.ir
        self.errors += new_info.errors
        self.warnings += new_info.warnings
        self.alev = new_info.alev
        self.diagnostics = self.gen_diagnostics()

    def gen_diagnostics(self) -> list[lspt.Diagnostic]:
        """Return diagnostics."""
        return [
            lspt.Diagnostic(
                range=create_range(error.loc),
                message=error.msg,
                severity=lspt.DiagnosticSeverity.Error,
            )
            for error in self.errors
        ] + [
            lspt.Diagnostic(
                range=create_range(warning.loc),
                message=warning.msg,
                severity=lspt.DiagnosticSeverity.Warning,
            )
            for warning in self.warnings
        ]


class JacLangServer(LanguageServer):
    """Class for managing workspace."""

    def __init__(self) -> None:
        """Initialize workspace."""
        super().__init__("jac-lsp", "v0.1")
        self.modules: dict[str, ModuleInfo] = {}

    def module_not_diff(self, uri: str, alev: ALev) -> bool:
        """Check if module was changed."""
        doc = self.workspace.get_text_document(uri)
        return (
            doc.uri in self.modules
            and self.modules[doc.uri].ir.source.hash
            == md5(doc.source.encode()).hexdigest()
            and (
                self.modules[doc.uri].alev >= alev
                or self.modules[doc.uri].has_syntax_error
            )
        )

    def push_diagnostics(self, file_path: str) -> None:
        """Push diagnostics for a file."""
        if file_path in self.modules:
            self.publish_diagnostics(
                file_path,
                self.modules[file_path].diagnostics,
            )

    def unwind_to_parent(self, file_path: str) -> str:
        """Unwind to parent."""
        orig_file_path = file_path
        if file_path in self.modules:
            while cur := self.modules[file_path].parent:
                file_path = cur.uri
            if file_path == orig_file_path and (
                discover := self.modules[file_path].ir.annexable_by
            ):
                file_path = uris.from_fs_path(discover)
                self.quick_check(file_path)
        return file_path

    def update_modules(
        self, file_path: str, build: Pass, alev: ALev, refresh: bool = False
    ) -> None:
        """Update modules."""
        if not isinstance(build.ir, ast.Module):
            self.log_error("Error with module build.")
            return
        new_mod = ModuleInfo(
            ir=build.ir,
            errors=[
                i
                for i in build.errors_had
                if i.loc.mod_path == uris.to_fs_path(file_path)
            ],
            warnings=[
                i
                for i in build.warnings_had
                if i.loc.mod_path == uris.to_fs_path(file_path)
            ],
            alev=alev,
        )
        if not refresh and file_path in self.modules:
            self.log_py(f"Before: {self.modules[file_path].warnings}")
            self.modules[file_path].update_with(new_mod)
            self.log_py(f"After: {self.modules[file_path].warnings}")
        else:
            self.modules[file_path] = new_mod
        for p in build.ir.mod_deps.keys():
            uri = uris.from_fs_path(p)
            new_mod = ModuleInfo(
                ir=build.ir.mod_deps[p],
                errors=[i for i in build.errors_had if i.loc.mod_path == p],
                warnings=[i for i in build.warnings_had if i.loc.mod_path == p],
                alev=alev,
            )
            if not refresh and uri in self.modules:
                self.modules[uri].update_with(new_mod)
            else:
                self.modules[uri] = new_mod
            self.modules[uri].parent = (
                self.modules[file_path] if file_path != uri else None
            )

    def quick_check(self, file_path: str, force: bool = False) -> None:
        """Rebuild a file."""
        if not force and self.module_not_diff(file_path, ALev.QUICK):
            return
        try:
            document = self.workspace.get_text_document(file_path)
            build = jac_str_to_pass(
                jac_str=document.source, file_path=document.path, schedule=[]
            )
        except Exception as e:
            self.log_error(f"Error during syntax check: {e}")
        self.update_modules(file_path, build, ALev.QUICK, refresh=True)

    def deep_check(self, file_path: str, force: bool = False) -> None:
        """Rebuild a file and its dependencies."""
        if file_path in self.modules:
            self.quick_check(file_path, force=force)
        if not force and self.module_not_diff(file_path, ALev.DEEP):
            return
        try:
            file_path = self.unwind_to_parent(file_path)
            build = jac_ir_to_pass(ir=self.modules[file_path].ir)
        except Exception as e:
            self.log_error(f"Error during syntax check: {e}")
        self.update_modules(file_path, build, ALev.DEEP)

    def type_check(self, file_path: str, force: bool = False) -> None:
        """Rebuild a file and its dependencies."""
        if file_path not in self.modules:
            self.deep_check(file_path, force=force)
        if not force and self.module_not_diff(file_path, ALev.TYPE):
            return
        try:
            file_path = self.unwind_to_parent(file_path)
            build = jac_ir_to_pass(
                ir=self.modules[file_path].ir, schedule=type_checker_sched
            )
        except Exception as e:
            self.log_error(f"Error during type check: {e}")
        self.update_modules(file_path, build, ALev.TYPE)

    def get_completion(
        self, file_path: str, position: lspt.Position
    ) -> lspt.CompletionList:
        """Return completion for a file."""
        items = []
        document = self.workspace.get_text_document(file_path)
        current_line = document.lines[position.line].strip()
        if current_line.endswith("hello."):

            items = [
                lspt.CompletionItem(label="world"),
                lspt.CompletionItem(label="friend"),
            ]
        return lspt.CompletionList(is_incomplete=False, items=items)

    def rename_module(self, old_path: str, new_path: str) -> None:
        """Rename module."""
        if old_path in self.modules and new_path != old_path:
            self.modules[new_path] = self.modules[old_path]
            del self.modules[old_path]

    def delete_module(self, uri: str) -> None:
        """Delete module."""
        if uri in self.modules:
            del self.modules[uri]

    def formatted_jac(self, file_path: str) -> list[lspt.TextEdit]:
        """Return formatted jac."""
        try:
            document = self.workspace.get_text_document(file_path)
            format = jac_str_to_pass(
                jac_str=document.source,
                file_path=document.path,
                target=JacFormatPass,
                schedule=[FuseCommentsPass, JacFormatPass],
            )
            formatted_text = (
                format.ir.gen.jac
                if JacParser not in [e.from_pass for e in format.errors_had]
                else document.source
            )
        except Exception as e:
            self.log_error(f"Error during formatting: {e}")
            formatted_text = document.source
        return [
            lspt.TextEdit(
                range=lspt.Range(
                    start=lspt.Position(line=0, character=0),
                    end=lspt.Position(
                        line=len(document.source.splitlines()) + 1, character=0
                    ),
                ),
                new_text=(formatted_text),
            )
        ]

    def get_hover_info(
        self, file_path: str, position: lspt.Position
    ) -> Optional[lspt.Hover]:
        """Return hover information for a file."""
        node_selected = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir, position.line, position.character
        )
        value = self.get_node_info(node_selected) if node_selected else None
        if value:
            return lspt.Hover(
                contents=lspt.MarkupContent(
                    kind=lspt.MarkupKind.PlainText, value=f"{value}"
                ),
            )
        return None

    def get_node_info(self, node: ast.AstSymbolNode) -> Optional[str]:
        """Extract meaningful information from the AST node."""
        self.log_py(f"Node selected: {node}")
        self.log_py(f"Node selected parent: {node.parent}")

        # self.log_py(f'varsss \n\n{vars(node)}')
        # self.log_py(f'\ndecl {node.sym.decl}')
        try:
            if node.parent and isinstance(node.parent,ast.ModulePath):
                self.log_py(f"path of is {node.parent.get_path(node.parent.path.index(node),self)}")
            if isinstance(node, ast.NameSpec):
                node = node.name_of
            access = node.sym.access.value + " " if node.sym else None
            node_info = (
                f"({access if access else ''}{node.sym_type.value}) {node.sym_name}"
            )
            if node.type_info.clean_type:
                node_info += f": {node.type_info.clean_type}"
            if isinstance(node, ast.AstSemStrNode) and node.semstr:
                node_info += f"\n{node.semstr.value}"
            if isinstance(node, ast.AstDocNode) and node.doc:
                node_info += f"\n{node.doc.value}"
            if isinstance(node, ast.Ability) and node.signature:
                node_info += f"\n{node.signature.unparse()}"
            self.log_py(f"mypy_node: {node.gen.mypy_ast}")
        except AttributeError as e:
            self.log_warning(f"Attribute error when accessing node attributes: {e}")
        return node_info.strip()

    def get_document_symbols(self, file_path: str) -> list[lspt.DocumentSymbol]:
        """Return document symbols for a file."""
        root_node = self.modules[file_path].ir.sym_tab
        if root_node:
            return collect_symbols(root_node)
        return []

    def get_definition(
        self, file_path: str, position: lspt.Position
    ) -> Optional[lspt.Location]:
        """Return definition location for a file."""
        node_selected: Optional[ast.AstSymbolNode] = find_deepest_symbol_node_at_pos(
            self.modules[file_path].ir, position.line, position.character
        )
        if node_selected:
            self.log_py(f"Node selected: {node_selected}")
            # self.log_py(f'varsss \n\n{vars(node_selected)}')
            if node_selected.parent and isinstance(node_selected.parent,ast.ModulePath):
                spec=node_selected.parent.get_path(node_selected.parent.path.index(node_selected),self)
                self.log_py(f"path of is in get defini\n\n\n {spec}\n\n")
                if spec:
                    return lspt.Location(
                        uri=uris.from_fs_path(spec),
                        range=lspt.Range(
                            start=lspt.Position(line=0, character=0),
                            end=lspt.Position(line=0, character=0),
                        ),
                    )
            if isinstance(node_selected, (ast.ElementStmt, ast.BuiltinType)):
                return None
            decl_node = (
                node_selected.parent.body.target
                if node_selected.parent
                and isinstance(node_selected.parent, ast.AstImplNeedingNode)
                and isinstance(node_selected.parent.body, ast.AstImplOnlyNode)
                else (
                    node_selected.sym.decl
                    if (node_selected.sym and node_selected.sym.decl)
                    else node_selected
                )
            )
            self.log_py(f"{node_selected}, {decl_node}")
            decl_uri = uris.from_fs_path(decl_node.loc.mod_path)
            try:
                decl_range = create_range(decl_node.loc)
            except ValueError:  # 'print' name has decl in 0,0,0,0
                return None
            decl_location = lspt.Location(
                uri=decl_uri,
                range=decl_range,
            )

            return decl_location
        else:
            self.log_info("No declaration found for the selected node.")
            return None

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.show_message_log(message, lspt.MessageType.Error)
        self.show_message(message, lspt.MessageType.Error)

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.show_message_log(message, lspt.MessageType.Warning)
        self.show_message(message, lspt.MessageType.Warning)

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.show_message_log(message, lspt.MessageType.Info)
        self.show_message(message, lspt.MessageType.Info)

    def log_py(self, message: str) -> None:
        """Log a message."""
        logging.info(message)
