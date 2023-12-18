"""Language tools for the Jaclang project."""

import ast as py_ast
import inspect
import os
import sys
from typing import List, Optional, Type

import jaclang.jac.absyntree as ast
from jaclang.jac.passes.tool.schedules import (
    AstDotGraphPass,
    AstPrinterPass,
    SymbolTableDotGraphPass,
    SymbolTablePrinterPass,
    full_ast_dot_gen,
    full_ast_print,
    sym_tab_dot_gen,
    sym_tab_print,
)
from jaclang.jac.transpiler import jac_file_to_pass
from jaclang.utils.helpers import pascal_to_snake


class AstKidInfo:
    """Information about a kid."""

    def __init__(self, name: str, typ: str, default: Optional[str] = None) -> None:
        """Initialize."""
        self.name = name
        self.typ = typ
        self.default = default


class AstNodeInfo:
    """Meta data about AST nodes."""

    type_map: dict[str, type] = {}

    def __init__(self, cls: type) -> None:
        """Initialize."""
        self.cls = cls
        self.process(cls)

    def process(self, cls: Type[ast.AstNode]) -> None:
        """Process AstNode class."""
        self.name = cls.__name__
        self.doc = cls.__doc__
        AstNodeInfo.type_map[self.name] = cls
        self.class_name_snake = pascal_to_snake(cls.__name__)
        self.init_sig = inspect.signature(cls.__init__)
        self.kids: list[AstKidInfo] = []
        for param_name, param in self.init_sig.parameters.items():
            if param_name not in [
                "self",
                "parent",
                "kid",
                "line",
                "sym_tab",
            ]:
                param_type = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else "Any"
                )
                param_default = (
                    param.default if param.default != inspect.Parameter.empty else None
                )
                self.kids.append(AstKidInfo(param_name, param_type, param_default))


class AstTool:
    """Ast tools."""

    def __init__(self) -> None:
        """Initialize."""
        module = sys.modules[ast.__name__]
        source_code = inspect.getsource(module)
        classes = inspect.getmembers(module, inspect.isclass)
        ast_node_classes = [
            AstNodeInfo(cls)
            for _, cls in classes
            if issubclass(cls, ast.AstNode)
            and cls.__name__
            not in [
                "AstNode",
                "OOPAccessNode",
                "WalkerStmtOnlyNode",
                "JacSource",
                "EmptyToken",
                "AstSymbolNode",
                "AstAccessNode",
                "TokenSymbol",
                "Literal",
                "AstDocNode",
                "PythonModuleAst",
                "AstAsyncNode",
                "AstElseBodyNode",
                "AstTypedVarNode",
                "AstImplOnlyNode",
                "Expr",
                "AtomExpr",
                "ElementStmt",
                "ArchBlockStmt",
                "EnumBlockStmt",
                "CodeBlockStmt",
                "NameSpec",
                "ArchSpec",
                "MatchPattern",
            ]
        ]

        self.ast_classes = sorted(
            ast_node_classes,
            key=lambda cls: source_code.find(f"class {cls.name}"),
        )

    def pass_template(self) -> str:
        """Generate pass template."""
        output = (
            "import jaclang.jac.absyntree as ast\n"
            "from jaclang.jac.passes import Pass\n\n"
            "class SomePass(Pass):\n"
        )

        def emit(to_append: str) -> None:
            """Emit to output."""
            nonlocal output
            output += "\n    " + to_append

        for cls in self.ast_classes:
            emit(
                f"def exit_{cls.class_name_snake}(self, node: ast.{cls.name}) -> None:"
            )
            emit('    """Sub objects.\n')

            for kid in cls.kids:
                emit(
                    f"    {kid.name}: {kid.typ}{' =' + str(kid.default) if kid.default else ''},"
                )

            emit('    """\n')
        output = (
            output.replace("jaclang.jac.absyntree.", "")
            .replace("typing.", "")
            .replace("<enum '", "")
            .replace("'>", "")
            .replace("<class '", "")
            .replace("ForwardRef('", "")
            .replace("')", "")
        )
        return output

    def py_ast_nodes(self) -> str:
        """List python ast nodes."""
        from jaclang.jac.passes.main import PyastBuildPass

        visit_methods = [
            method for method in dir(py_ast._Unparser) if method.startswith("visit_")  # type: ignore
        ]
        node_names = [method.replace("visit_", "") for method in visit_methods]
        pass_func_names = []
        for name, value in inspect.getmembers(PyastBuildPass):
            if name.startswith("proc_") and inspect.isfunction(value):
                pass_func_names.append(name.replace("proc_", ""))
        output = ""
        missing = []
        for i in node_names:
            nd = pascal_to_snake(i)
            this_func = (
                f"def proc_{nd}(self, node: py_ast.{i}) -> ast.AstNode:\n"
                + '    """Process python node."""\n\n'
            )
            if nd not in pass_func_names:
                missing.append(this_func)
            output += this_func
        for i in missing:
            output += f"# missing: \n{i}\n"
        return output

    def md_doc(self) -> str:
        """Generate mermaid markdown doc."""
        output = ""
        for cls in self.ast_classes:
            if not len(cls.kids):
                continue
            output += f"## {cls.name}\n"
            output += "```mermaid\nflowchart LR\n"
            for kid in cls.kids:
                if "_end" in kid.name:
                    kid.name = kid.name.replace("_end", "_end_")
                arrow = "-.->" if "Optional" in kid.typ else "-->"
                typ = (
                    kid.typ.replace("Optional[", "")
                    .replace("SubNodeList[", "")
                    .replace("SubTag[", "")
                    .replace("Sequence[", "")
                    .replace("]", "")
                    .replace("|", ",")
                    .replace("list[", "list - ")
                )
                output += f"{cls.name} {arrow}|{typ}| {kid.name}\n"
            output += "```\n\n"
            output += f"{cls.doc} \n\n"
        return output

    def gen_dotfile(self, args: List[str]) -> str:
        """Generate a dot file for AST."""
        if len(args) == 0:
            return "Usage: gen_dotfile <file_path> [<output_path>]"

        file_name: str = args[0]
        AstDotGraphPass.OUTPUT_FILE_PATH = args[1] if len(args) == 2 else None

        if not os.path.isfile(file_name):
            return f"Error: {file_name} not found"

        if file_name.endswith(".jac"):
            [base, mod] = os.path.split(file_name)
            base = base if base else "./"
            jac_file_to_pass(file_name, AstDotGraphPass, full_ast_dot_gen)
            if AstDotGraphPass.OUTPUT_FILE_PATH:
                return f"Dot file generated at {AstDotGraphPass.OUTPUT_FILE_PATH}"
            else:
                return ""
        else:
            return "Not a .jac file."

    def print(self, args: List[str]) -> str:
        """Generate a dot file for AST."""
        if len(args) == 0:
            return "Usage: print <file_path>"

        file_name: str = args[0]

        if not os.path.isfile(file_name):
            return f"Error: {file_name} not found"

        if file_name.endswith(".jac"):
            [base, mod] = os.path.split(file_name)
            base = base if base else "./"
            jac_file_to_pass(file_name, AstPrinterPass, full_ast_print)
            return ""
        else:
            return "Not a .jac file."

    def symtab_print(self, args: List[str]) -> str:
        """Generate a dot file for AST."""
        if len(args) == 0:
            return "Usage: print <file_path>"

        file_name: str = args[0]

        if not os.path.isfile(file_name):
            return f"Error: {file_name} not found"

        if file_name.endswith(".jac"):
            [base, mod] = os.path.split(file_name)
            base = base if base else "./"
            jac_file_to_pass(file_name, SymbolTablePrinterPass, sym_tab_print)
            return ""
        else:
            return "Not a .jac file."

    def gen_symtab_dotfile(self, args: List[str]) -> str:
        """Generate a dot file for Symbol Table."""
        if len(args) == 0:
            return "Usage: gen_dotfile <file_path> [<output_path>]"

        file_name: str = args[0]
        SymbolTableDotGraphPass.OUTPUT_FILE_PATH = args[1] if len(args) == 2 else None

        if not os.path.isfile(file_name):
            return f"Error: {file_name} not found"

        if file_name.endswith(".jac"):
            [base, mod] = os.path.split(file_name)
            base = base if base else "./"
            jac_file_to_pass(file_name, SymbolTableDotGraphPass, sym_tab_dot_gen)
            if SymbolTableDotGraphPass.OUTPUT_FILE_PATH:
                return (
                    f"Dot file generated at {SymbolTableDotGraphPass.OUTPUT_FILE_PATH}"
                )
            else:
                return ""
        else:
            return "Not a .jac file."

    def automate_ref(self):
        def extract_headings(file_path):
            with open(file_path, "r") as file:
                lines = file.readlines()

            headings = {}
            current_heading = None
            for idx, line in enumerate(lines, start=1):
                if line.startswith("//"):
                    if current_heading is not None:
                        headings[current_heading] = (
                            start_line,
                            idx - 2,
                        )  # Subtract 1 to get the correct end line
                    current_heading = line.strip("//").strip()
                    start_line = idx + 1

            # Add the last heading
            if current_heading is not None:
                headings[current_heading] = (start_line, len(lines))

            return headings

        # Jac lark path
        file_path = os.path.join(
            os.path.split(os.path.dirname(__file__))[0], "../jaclang/jac/jac.lark"
        )

        result = extract_headings(file_path)

        created_file_path = os.path.join(
            os.path.split(os.path.dirname(__file__))[0],
            "../support/jac-lang.org/docs/learn/jac_ref.md",
        )

        with open(created_file_path, "w") as md_file:
            # Write the content to the destination file
            md_file.write("# Jac Language Reference \n\n## Introduction \n\n")

        for heading, lines in result.items():
            print(f"{heading}: {lines}")
            content = f'## {heading}\n```yaml linenums="{lines[0]}"\n--8<-- "jaclang/jac/jac.lark:{lines[0]}:{lines[1]}"\n```\n\n=== "jac"\n    ```jac linenums="1"\n    --8<-- "examples/reference/{heading}.jac"\n    ```\n=== "python"\n    ```python linenums="1"\n    --8<-- "examples/reference/{heading}.py"\n    ```\n'
            with open(created_file_path, "a") as md_file:
                # Write the content to the destination file
                md_file.write(f"{content}\n")
