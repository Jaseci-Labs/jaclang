"""Jac Symbol Table."""

from __future__ import annotations

import ast as ast3
from typing import Optional, Sequence

import jaclang.compiler.absyntree as ast
from jaclang.compiler.constant import SymbolAccess, SymbolType
from jaclang.utils.treeprinter import dotgen_symtab_tree, print_symtab_tree


# Symbols can have mulitple definitions but resolves decl to be the
# first such definition in a given scope.
class Symbol:
    """Symbol."""

    def __init__(
        self,
        defn: ast.NameAtom,
        access: SymbolAccess,
        parent_tab: SymbolTable,
    ) -> None:
        """Initialize."""
        self.defn: list[ast.NameAtom] = [defn]
        self.uses: list[ast.NameAtom] = []
        defn.sym = self
        self.access: SymbolAccess = access
        self.parent_tab = parent_tab

    @property
    def decl(self) -> ast.NameAtom:
        """Get decl."""
        return self.defn[0]

    @property
    def sym_name(self) -> str:
        """Get name."""
        return self.decl.sym_name

    @property
    def sym_type(self) -> SymbolType:
        """Get sym_type."""
        return self.decl.sym_category

    @property
    def sym_dotted_name(self) -> str:
        """Return a full path of the symbol."""
        out = [self.defn[0].sym_name]
        current_tab = self.parent_tab
        while current_tab is not None:
            out.append(current_tab.name)
            if current_tab.has_parent():
                current_tab = current_tab.parent
            else:
                break
        out.reverse()
        return ".".join(out)

    def add_defn(self, node: ast.NameAtom) -> None:
        """Add defn."""
        self.defn.append(node)
        node.sym = self

    def add_use(self, node: ast.NameAtom) -> None:
        """Add use."""
        self.uses.append(node)
        node.sym = self

    def __repr__(self) -> str:
        """Repr."""
        return f"Symbol({self.sym_name}, {self.sym_type}, {self.access}, {self.defn})"


class SymbolTable:
    """Symbol Table."""

    def __init__(
        self, name: str, owner: ast.AstNode, parent: Optional[SymbolTable] = None
    ) -> None:
        """Initialize."""
        self.name = name
        self.owner = owner
        self.parent = parent if parent else self
        self.kid: list[SymbolTable] = []
        self.tab: dict[str, Symbol] = {}
        self.inherit: list[SymbolTable] = []

    def has_parent(self) -> bool:
        """Check if has parent."""
        return self.parent != self

    def get_parent(self) -> SymbolTable:
        """Get parent."""
        if self.parent == self:
            raise Exception("No parent")
        return self.parent

    def lookup(self, name: str, deep: bool = True) -> Optional[Symbol]:
        """Lookup a variable in the symbol table."""
        if name in self.tab:
            return self.tab[name]
        for i in self.inherit:
            found = i.lookup(name, deep=False)
            if found:
                return found
        if deep and self.has_parent():
            return self.get_parent().lookup(name, deep)
        return None

    def insert(
        self,
        node: ast.AstSymbolNode,
        access_spec: Optional[ast.AstAccessNode] | SymbolAccess = None,
        single: bool = False,
    ) -> Optional[ast.AstNode]:
        """Set a variable in the symbol table.

        Returns original symbol as collision if single check fails, none otherwise.
        Also updates node.sym to create pointer to symbol.
        """
        collision = (
            self.tab[node.sym_name].defn[-1]
            if single and node.sym_name in self.tab
            else None
        )
        if node.sym_name not in self.tab:
            self.tab[node.sym_name] = Symbol(
                defn=node.name_spec,
                access=(
                    access_spec
                    if isinstance(access_spec, SymbolAccess)
                    else access_spec.access_type if access_spec else SymbolAccess.PUBLIC
                ),
                parent_tab=self,
            )
        else:
            self.tab[node.sym_name].add_defn(node.name_spec)
        node.name_spec.sym = self.tab[node.sym_name]
        return collision

    def find_scope(self, name: str) -> Optional[SymbolTable]:
        """Find a scope in the symbol table."""
        for k in self.kid:
            if k.name == name:
                return k
        return None

    def push_scope(self, name: str, key_node: ast.AstNode) -> SymbolTable:
        """Push a new scope onto the symbol table."""
        self.kid.append(SymbolTable(name, key_node, self))
        return self.kid[-1]

    def inherit_sym_tab(self, target_scope: SymbolTable, sym_tab: SymbolTable) -> None:
        """Inherit symbol table."""
        for i in sym_tab.tab.values():
            self.def_insert(i.decl, access_spec=i.access, table_override=target_scope)

    def def_insert(
        self,
        node: ast.AstSymbolNode,
        access_spec: Optional[ast.AstAccessNode] | SymbolAccess = None,
        single_decl: Optional[str] = None,
        table_override: Optional[SymbolTable] = None,
    ) -> Optional[Symbol]:
        """Insert into symbol table."""
        table = table_override if table_override else node.sym_tab
        if node.sym and table == node.sym.parent_tab:
            return node.sym
        if table:
            table.insert(
                node=node, single=single_decl is not None, access_spec=access_spec
            )
        node.make_store_ctx()
        return node.sym

    def chain_def_insert(self, node_list: Sequence[ast.AstSymbolNode]) -> None:
        """Link chain of containing names to symbol."""
        if not node_list:
            return
        cur_sym_tab = node_list[0].sym_tab
        node_list[-1].name_spec.py_ctx_func = ast3.Store
        if isinstance(node_list[-1].name_spec, ast.AstSymbolNode):
            node_list[-1].name_spec.py_ctx_func = ast3.Store

        node_list = node_list[:-1]  # Just performs lookup mappings of pre assign chain
        for i in node_list:
            if cur_sym_tab is None:
                break
            cur_sym_tab = (
                lookup.decl.sym_tab
                if (
                    lookup := self.use_lookup(
                        i,
                        sym_table=cur_sym_tab,
                    )
                )
                else None
            )

    def use_lookup(
        self,
        node: ast.AstSymbolNode,
        sym_table: Optional[SymbolTable] = None,
    ) -> Optional[Symbol]:
        """Link to symbol."""
        if node.sym:
            return node.sym
        if not sym_table:
            sym_table = node.sym_tab
        if sym_table:
            lookup = sym_table.lookup(name=node.sym_name, deep=True)
            lookup.add_use(node.name_spec) if lookup else None
        return node.sym

    def chain_use_lookup(self, node_list: Sequence[ast.AstSymbolNode]) -> None:
        """Link chain of containing names to symbol."""
        if not node_list:
            return
        cur_sym_tab = node_list[0].sym_tab
        for i in node_list:
            if cur_sym_tab is None:
                break
            cur_sym_tab = (
                lookup.decl.sym_tab
                if (
                    lookup := self.use_lookup(
                        i,
                        sym_table=cur_sym_tab,
                    )
                )
                else None
            )

    def pp(self, depth: Optional[int] = None) -> str:
        """Pretty print."""
        return print_symtab_tree(root=self, depth=depth)

    def dotgen(self) -> str:
        """Generate dot graph for sym table."""
        return dotgen_symtab_tree(self)

    def __repr__(self) -> str:
        """Repr."""
        out = f"{self.name} {super().__repr__()}:\n"
        for k, v in self.tab.items():
            out += f"    {k}: {v}\n"
        return out


__all__ = [
    "Symbol",
    "SymbolTable",
    "SymbolType",
    "SymbolAccess",
]
