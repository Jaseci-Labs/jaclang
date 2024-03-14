# this is a test module to test
# import sys

from jaclang.jac.passes.tool import (
    JacFormatPass,
)
from jaclang.jac.passes.tool.schedules import format_pass
from jaclang.jac.transpiler import jac_file_formatter, jac_file_to_pass

# from jaclang.jac.passes.tool.schedules import format_pass, py_code_gen

# from jaclang.jac.transpiler import jac_file_formatter

input_file_path = "/home/ubuntu/jaclang_new/jaclang/examples/reference/assignment.jac"
# code_gen = jac_file_formatter(input_file_path)
code_gen = jac_file_to_pass(file_path=input_file_path, schedule=format_pass)
print(code_gen.ir.gen.jac)
print(code_gen.errors_had)


# import jaclang.jac.absyntree as ast
# from jaclang.jac.passes import Pass


# class FormatPass(Pass):
#     def exit_token(self, node: ast.Token) -> None:
#         """Sub objects.

#         name: str,
#         value: str,
#         col_start: int,
#         col_end: int,
#         """
#         self.emit(node, node.value)

#     def exit_name(self, node: ast.Name) -> None:
#         """Sub objects.

#         name: str,
#         value: str,
#         col_start: int,
#         col_end: int,
#         already_declared: bool,
#         """
#         self.emit(node, node.value)

#     def exit_constant(self, node: ast.Constant) -> None:
#         """Sub objects.

#         name: str,
#         value: str,
#         col_start: int,
#         col_end: int,
#         typ: type,
#         """
#         self.emit(node, node.value)

#     def exit_module(self, node: ast.Module) -> None:
#         """Sub objects.

#         name: str,
#         doc: Token,
#         body: "Elements",
#         """
#         self.emit_ln(node, node.doc.value)
#         self.emit(node, self.preamble.meta["py_code"])
#         if node.body:
#             self.emit(node, node.body.meta["py_code"])
#         self.emit(node, f"\n")
#         for i in self.debuginfo["jac_mods"]:
#             self.emit(node, f"{i}\n")
#         self.emit(node, "\n")
#         self.ir = node
#         self.ir.meta["py_code"] = self.ir.meta["py_code"].rstrip()

#     def exit_elements(self, node: ast.Elements) -> None:
#         """Sub objects.

#         elements: list[GlobalVars |
#         Test | ModuleCode | Import | Architype | Ability | AbilitySpec],
#         """
#         for i in node.elements:
#             self.emit(node, i.meta["py_code"])
#             self.emit(node, "\n")

#     def exit_module_code(self, node: ast.ModuleCode) -> None:
#         """Sub objects.

#         doc: Optional[Token],
#         name: Optional[Name],
#         body: CodeBlock,

#         """
#         if node.doc:
#             self.emit_ln(node, node.doc.value)
#             print("in doc")
#         if node.name:
#             print("i'm here")
#             self.emit_ln(node, f"if __name__ == '{node.name.meta['py_code']}':")
#             self.indent_level += 1
#             self.emit(node, node.body.meta["py_code"])
#             self.indent_level -= 1
#         else:
#             print("in else")
#             self.emit(node, node.body.meta["py_code"])

#     def exit_code_block(self, node: ast.CodeBlock) -> None:
#         """Sub objects.

#         stmts: list["StmtType"],
#         """
#         if len(node.stmts) == 0:
#             self.emit_ln(node, "pass")
#         for i in node.stmts:
#             self.emit(node, i.meta["py_code"])
#             if len(i.meta["py_code"]) and i.meta["py_code"][-1] != "\n":
#                 self.emit_ln(node, "\n")

#     def exit_func_call(self, node: ast.FuncCall) -> None:
#         """Sub objects.

#         target: AtomType,
#         params: Optional[ParamList],
#         """
#         if node.params:
#             self.emit(
#                 node,
#                 f"{node.target.meta['py_code']}({node.params.meta['py_code']})",
#             )
#         else:
#             self.emit(node, f"{node.target.meta['py_code']}()")

#     def exit_param_list(self, node: ast.ParamList) -> None:
#         """Sub objects.

#         p_args: Optional[ExprList],
#         p_kwargs: Optional[AssignmentList],
#         """
#         if node.p_args and node.p_kwargs:
#             self.emit(
#                 node,
#                 f"{node.p_args.meta['py_code']}, {node.p_kwargs.meta['py_code']}",
#             )
#         elif node.p_args:
#             self.emit(node, f"{node.p_args.meta['py_code']}")
#         elif node.p_kwargs:
#             self.emit(node, f"{node.p_kwargs.meta['py_code']}")

#     def exit_expr_list(self, node: ast.ExprList) -> None:
#         """Sub objects.

#         values: list[ExprType],
#         """
#         self.emit(
#             node, f"{', '.join([value.meta['py_code'] for value in node.values])}"
#         )

#     def exit_multi_string(self, node: ast.MultiString) -> None:
#         """Sub objects.

#         strings: list[Token],
#         """
#         for string in node.strings:
#             self.emit(node, string.meta["py_code"])

#     def before_pass(self) -> None:
#         """Initialize pass."""
#         self.indent_size = 4
#         self.indent_level = 0
#         self.debuginfo = {"jac_mods": []}
#         self.preamble = ast.AstNode(parent=None, mod_link=None, kid=[], line=0)
#         self.preamble.meta["py_code"] = ""
#         self.cur_arch = None  # tracks current architype during transpilation

#     def enter_node(self, node: ast.AstNode) -> None:
#         """Enter node."""
#         if node:
#             node.meta["py_code"] = ""
#         print(f"Entering node: {node}")
#         return Pass.enter_node(self, node)

#     def indent_str(self) -> str:
#         """Return string for indent."""
#         return " " * self.indent_size * self.indent_level

#     def emit_ln(self, node: ast.AstNode, s: str) -> None:
#         """Emit code to node."""
#         self.emit(node, s.strip().strip("\n"))
#         self.emit(node, f"  # {self.get_mod_index(node)} {node.line}\n")

#     def emit_ln_unique(self, node: ast.AstNode, s: str) -> None:
#         """Emit code to node."""
#         if s not in node.meta["py_code"]:
#             ilev = self.indent_level
#             self.indent_level = 0
#             self.emit_ln(node, s)
#             self.indent_level = ilev

#     def get_mod_index(self, node: ast.AstNode) -> int:
#         """Get module index."""
#         path = node.mod_link.mod_path if node.mod_link else None
#         if not path:
#             return -1
#         if path not in self.debuginfo["jac_mods"]:
#             self.debuginfo["jac_mods"].append(path)
#         return self.debuginfo["jac_mods"].index(path)

#     def emit(self, node: ast.AstNode, s: str) -> None:
#         """Emit code to node."""
#         node.meta["py_code"] += self.indent_str() + s.replace(
#             "\n", "\n" + self.indent_str()
#         )
#         if "\n" in node.meta["py_code"]:
#             node.meta["py_code"] = node.meta["py_code"].rstrip(" ")
