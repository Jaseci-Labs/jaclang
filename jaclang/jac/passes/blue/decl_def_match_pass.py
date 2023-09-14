"""Connect Decls and Defs in AST."""
import jaclang.jac.absyntree as ast
from jaclang.jac.passes import Pass
from jaclang.jac.passes.blue import SubNodeTabPass
from jaclang.jac.sym_table import DefDeclSymbol


class DeclDefMatchPass(Pass):
    """Decls and Def matching pass."""

    def after_pass(self) -> None:
        """Rebuild sub node table."""
        self.ir = SubNodeTabPass(mod_path=self.mod_path, input_ir=self.ir).ir

    def exit_global_vars(self, node: ast.GlobalVars) -> None:
        """Sub objects.

        doc: Optional[DocString],
        access: Optional[Token],
        assignments: AssignmentList,
        """
        for i in self.get_all_sub_nodes(node, ast.Assignment):
            if not isinstance(i.target, ast.Name):
                self.ice(
                    "Only name targets should be possible to assign in global vars."
                )
            else:
                decl = self.sym_tab.lookup(i.target.value)
                if decl:
                    if decl.has_def:
                        self.error(f"Name {i.target.value} already bound.")
                    else:
                        decl.has_def = True
                        decl.other_node = i
                        decl.node.body = i  # TODO: I dont think this line makes sense
                        self.sym_tab.set(decl)

    def exit_test(self, node: ast.Test) -> None:
        """Sub objects.

        name: Name,
        doc: Optional[DocString],
        description: Token,
        body: CodeBlock,
        """

    def enter_import(self, node: ast.Import) -> None:
        """Sub objects.

        lang: Name,
        path: ModulePath,
        alias: Optional[Name],
        items: Optional[ModuleItems],
        is_absorb: bool,
        sub_module: Optional[Module],
        """
        if not node.is_absorb:
            self.sym_tab = self.sym_tab.push(node.path.path_str)

    def exit_import(self, node: ast.Import) -> None:
        """Sub objects.

        lang: Name,
        path: ModulePath,
        alias: Optional[Name],
        items: Optional[ModuleItems],
        is_absorb: bool,
        sub_module: Optional[Module],
        """
        if not node.is_absorb and not self.sym_tab.parent:
            self.ice("Import should have a parent sym_table scope.")
        elif not node.is_absorb:
            self.sym_tab = self.sym_tab.pop()
        if node.items:  # now treat imported items as global
            for i in node.items.items:
                name = i.alias if i.alias else i.name
                decl = self.sym_tab.lookup(name.value)
                if not decl:
                    self.sym_tab.set(
                        DefDeclSymbol(name=name.value, node=i, has_def=True)
                    )

    def exit_module_item(self, node: ast.ModuleItem) -> None:
        """Sub objects.

        name: Name,
        alias: Optional[Token],
        body: Optional[AstNode],
        """
        if not self.sym_tab.lookup(node.name.value):
            self.sym_tab.set(
                DefDeclSymbol(name=node.name.value, node=node, has_decl=True)
            )

    def exit_architype(self, node: ast.Architype) -> None:
        """Sub objects.

        name: Name,
        arch_type: Token,
        doc: Optional[DocString],
        decorators: Optional[Decorators],
        access: Optional[Token],
        base_classes: BaseClasses,
        body: Optional[ArchBlock],
        """
        # if no body, check for def
        #    if no def, register as decl
        # if complete register as def
        # nota: can allow static overriding perhaps?
        # note: if arch has not body ok, imports body is the arch itself

    def exit_arch_def(self, node: ast.ArchDef) -> None:
        """Sub objects.

        doc: Optional[DocString],
        mod: Optional[DottedNameList],
        arch: ObjectRef | NodeRef | EdgeRef | WalkerRef,
        body: ArchBlock,
        """

    def enter_ability(self, node: ast.Ability) -> None:
        """Sub objects.

        name_ref: Name | SpecialVarRef | ArchRef,
        is_func: bool,
        is_async: bool,
        is_static: bool,
        doc: Optional[Token],
        decorators: Optional["Decorators"],
        access: Optional[Token],
        signature: Optional["FuncSignature | TypeSpec | EventSignature"],
        body: Optional["CodeBlock"],

        arch_attached: Optional["ArchBlock"] = None,
        """
        self.sym_tab = self.sym_tab.push(node.py_resolve_name())

    def exit_ability(self, node: ast.Ability) -> None:
        """Sub objects.

        name: Name,
        is_func: bool,
        doc: Optional[DocString],
        decorators: Optional["Decorators"],
        access: Optional[Token],
        signature: "FuncSignature | TypeSpec | EventSignature",
        body: Optional["CodeBlock"],
        arch_attached: Optional["ArchBlock"] = None,
        """
        self.sym_tab = self.sym_tab.pop()
        ability_name = node.py_resolve_name()
        name = (
            f"{node.arch_attached.parent.name.value}.{ability_name}"
            if node.arch_attached
            and isinstance(node.arch_attached.parent, ast.Architype)
            else ability_name
        )
        decl = self.sym_tab.lookup(name)
        if decl and decl.has_decl:
            self.error(
                f"Ability bound with name {name} already defined on "
                f"Line {decl.node.line} in {decl.node.mod_link.rel_mod_path}."
            )
        elif decl and decl.has_def:
            decl.has_decl = True
            decl.node = node
            decl.node.body = (
                decl.other_node.body
                if isinstance(decl.other_node, ast.AbilityDef)
                else self.ice("Expected node of type AbilityDef in symbol table.")
            )
            ast.append_node(decl.node, decl.other_node)
            self.sym_tab.set(decl)
        else:
            decl = DefDeclSymbol(name=name, node=node, has_decl=True)
            if node.body:
                decl.has_def = True
                decl.other_node = node
            self.sym_tab.set(decl)

    def enter_ability_def(self, node: ast.AbilityDef) -> None:
        """Sub objects.

        doc: Optional[DocString],
        target: Optional["DottedNameList"],
        ability: "ArchRef",
        signature: "FuncSignature | EventSignature",
        body: "CodeBlock",
        """
        self.sym_tab = self.sym_tab.push(node.ability.py_resolve_name())

    def exit_ability_def(self, node: ast.AbilityDef) -> None:
        """Sub objects.

        doc: Optional[DocString],
        target: Optional["DottedNameList"],
        ability: "ArchRef",
        signature: "FuncSignature | EventSignature",
        body: "CodeBlock",
        """
        self.sym_tab = self.sym_tab.pop()
        name = node.ability.py_resolve_name()
        if node.target:
            owner = node.target.names[-1]
            if not isinstance(owner, ast.ArchRef):
                self.error("Expected reference to Architype!")
                owner = ""
            else:
                owner = owner.py_resolve_name()
            name = f"{owner}.{name}"
        decl = self.sym_tab.lookup(name)
        if decl and decl.has_def:
            self.error(
                f"Ability bound with name {name} already defined on "
                f"Line {decl.other_node.line} in {decl.other_node.mod_link.rel_mod_path}."
            )
        elif decl and decl.has_decl:
            decl.has_def = True
            decl.other_node = node
            decl.node.body = decl.other_node.body
            ast.append_node(decl.node, decl.other_node)
            self.sym_tab.set(decl)
        else:
            self.sym_tab.set(DefDeclSymbol(name=name, other_node=node, has_def=True))

    def enter_arch_block(self, node: ast.ArchBlock) -> None:
        """Sub objects.

        members: list['ArchHas | Ability'],
        """
        # Tags all function signatures whether method style or not
        for i in self.get_all_sub_nodes(node, ast.Ability):
            i.arch_attached = node

    def exit_enum(self, node: ast.Enum) -> None:
        """Sub objects.

        name: Name,
        doc: Optional[DocString],
        decorators: Optional[Decorators],
        access: Optional[Token],
        base_classes: BaseClasses,
        body: Optional[EnumBlock],
        """
        name = node.name.value
        decl = self.sym_tab.lookup(name)
        if decl and decl.has_decl:
            self.error(
                f"Enum bound with name {name} already defined on Line {decl.node.line}."
            )
        elif decl and decl.has_def:
            decl.has_decl = True
            decl.node = node
            decl.node.body = (
                decl.other_node.body
                if isinstance(decl.other_node, ast.EnumDef)
                else self.ice("Expected node of type EnumDef in symbol table.")
            )
            ast.append_node(decl.node, decl.other_node)
            self.sym_tab.set(decl)
        else:
            decl = DefDeclSymbol(name=name, node=node, has_decl=True)
            if node.body:
                decl.has_def = True
                decl.other_node = node
            self.sym_tab.set(decl)

    def exit_enum_def(self, node: ast.EnumDef) -> None:
        """Sub objects.

        doc: Optional[Token],
        enum: ArchRef,
        mod: Optional[DottedNameList],
        body: EnumBlock,
        """
        name = node.enum.py_resolve_name()
        decl = self.sym_tab.lookup(name)
        if decl and decl.has_def:
            self.error(
                f"Enum bound with name {name} already defined on Line {decl.other_node.line}."
            )
        elif decl and decl.has_decl:
            decl.has_def = True
            decl.other_node = node
            decl.node.body = decl.other_node.body
            ast.append_node(decl.node, decl.other_node)
            self.sym_tab.set(decl)
        else:
            self.sym_tab.set(DefDeclSymbol(name=name, other_node=node, has_def=True))
