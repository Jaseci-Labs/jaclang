from __future__ import annotations
from jaclang.plugin.feature import JacFeature as _Jac
from jaclang.plugin.builtin import *
from dataclasses import dataclass as __jac_dataclass__


def print_base_classes(cls: type) -> type:
    print(f"Base classes of {cls.__name__}: {[c.__name__ for c in cls.__bases__]}")
    return cls


@_Jac.make_obj(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class Animal:
    pass


@_Jac.make_obj(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class Domesticated:
    pass


@print_base_classes
@_Jac.make_node(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class Mammal(Animal, Domesticated):
    pass


@_Jac.make_walker(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class Dog(Mammal):
    pass


@_Jac.make_walker(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class Labrador(Dog):
    pass


@print_base_classes
@_Jac.make_walker(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class DecoratedLabrador(Labrador):
    pass


@__jac_dataclass__(eq=False)
class School:
    pass


@print_base_classes
@_Jac.make_edge(on_entry=[], on_exit=[])
@__jac_dataclass__(eq=False)
class student(School):
    pass
