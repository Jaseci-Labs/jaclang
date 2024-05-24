"""Special Imports for Jac Code."""

import types
from typing import Optional, Union

from jaclang.compiler.absyntree import Module

from .machine import machine


def jac_importer(
    target: str,
    base_path: str,
    absorb: bool = False,
    cachable: bool = True,
    mdl_alias: Optional[str] = None,
    override_name: Optional[str] = None,
    mod_bundle: Optional[Module] = None,
    lng: Optional[str] = "jac",
    items: Optional[dict[str, Union[str, bool]]] = None,
) -> Optional[types.ModuleType]:
    """Core Import Process."""
    program = machine.load_program(
        filename=target,
        base_path=base_path,
        cachable=cachable,
        override_name=override_name,
        mod_bundle=mod_bundle,
        lng=lng,
        items=items,
        absorb=absorb,
        mdl_alias=mdl_alias,
    )
    return program.module
