"""Transpilation functions."""
from typing import Type, TypeVar, List

import jaclang.jac.absyntree as ast
from jaclang.jac.parser import JacLexer
from jaclang.jac.parser import JacParser
from jaclang.jac.passes import Pass
from jaclang.jac.passes.blue import BluePygenPass, pass_schedule as blue_pass_schedule
from jaclang.jac.transform import Transform


T = TypeVar("T", bound=Pass)

class Transpiler:
    @staticmethod
    def _to_parse_tree(file_path: str, base_dir: str) -> Transform:
        """Convert a Jac file to an AST."""
        with open(file_path) as file:
            lex = JacLexer(mod_path=file_path, input_ir=file.read(), base_path=base_dir)
            prse = JacParser(
                mod_path=file_path, input_ir=lex.ir, base_path=base_dir, prior=lex
            )
            return prse
    
    @staticmethod
    def to_pass(file_path: str, base_dir: str = '', target: Type[T] = BluePygenPass, pass_schedule: List[Type[T]] = blue_pass_schedule)-> T:
        """Convert a Jac file to an AST."""
        ast_ret = Transpiler._to_parse_tree(file_path, base_dir)
        for i in pass_schedule:
            if i == target:
                break
            ast_ret = i(
                mod_path=file_path, input_ir=ast_ret.ir, base_path=base_dir, prior=ast_ret
            )
        ast_ret = target(
            mod_path=file_path, input_ir=ast_ret.ir, base_path=base_dir, prior=ast_ret
        )
        return ast_ret
    
    @staticmethod
    def transpile(file_path: str, base_dir: str = '', pass_schedule: List[Type[T]] = blue_pass_schedule, target: Type[T] = BluePygenPass) -> Transform:
        """Transpiler Jac file and return python code as string."""
        code = Transpiler.to_pass(file_path=file_path, base_dir=base_dir, target=target, pass_schedule = pass_schedule)
        if isinstance(code.ir, ast.Module):
            return code.ir.meta["py_code"]
        else:
            raise code.gen_exception("Transpilation of Jac file failed.")