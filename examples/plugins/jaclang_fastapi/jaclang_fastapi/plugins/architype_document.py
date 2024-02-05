from jaclang.core.construct import Architype, DSFunc, NodeArchitype

from typing import Type, Callable
from jaclang.plugin.default import hookimpl
from jaclang.plugin.feature import JacFeature as Jac


class JacPlugin:
    pass

    @staticmethod
    @hookimpl
    def make_node(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]:
        """Create a obj architype."""

        def decorator(cls: Type[Architype]) -> Type[Architype]:
            """Decorate class."""
            cls = Jac.make_architype(
                cls=cls, arch_base=NodeArchitype, on_entry=on_entry, on_exit=on_exit
            )
            return cls

        return decorator
