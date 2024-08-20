import types
from _typeshed import Incomplete
from jaclang.compiler.absyntree import Module as Module
from jaclang.compiler.compile import compile_jac as compile_jac
from jaclang.utils.log import logging as logging

logger: Incomplete

class JacMachine:
    base_path: Incomplete
    base_path_dir: Incomplete
    jac_program: Incomplete
    def __init__(self, base_path: str = "") -> None: ...
    def attach_program(self, jac_program: JacProgram) -> None: ...
    def get_mod_bundle(self) -> Module | None: ...
    def get_bytecode(
        self, module_name: str, full_target: str, caller_dir: str, cachable: bool = True
    ) -> types.CodeType | None: ...

class JacProgram:
    mod_bundle: Incomplete
    bytecode: Incomplete
    def __init__(
        self, mod_bundle: Module | None, bytecode: dict[str, bytes] | None
    ) -> None: ...
    def get_bytecode(
        self, module_name: str, full_target: str, caller_dir: str, cachable: bool = True
    ) -> types.CodeType | None: ...
