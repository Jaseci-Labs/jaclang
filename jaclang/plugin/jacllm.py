
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


class JacLLM:
    """Jac LLM."""

    @staticmethod
    def get_semstr_type(
        file_loc: str, scope: str, attr: str, return_semstr: bool
    ) -> Optional[str]:
        from jaclang.plugin.feature import pm

        """Jac's get_semstr_type feature."""
        return pm.hook.get_semstr_type(
            file_loc=file_loc, scope=scope, attr=attr, return_semstr=return_semstr
        )

    @staticmethod
    def obj_scope(file_loc: str, attr: str) -> str:
        """Jac's get_semstr_type feature."""
        from jaclang.plugin.feature import pm
        return pm.hook.obj_scope(file_loc=file_loc, attr=attr)

    @staticmethod
    def get_sem_type(file_loc: str, attr: str) -> tuple[str | None, str | None]:
        """Jac's get_semstr_type feature."""
        from jaclang.plugin.feature import pm
        return pm.hook.get_sem_type(file_loc=file_loc, attr=attr)