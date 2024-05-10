"""JacLLM : Jac s LLM."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from jaclang.core.aott import LLMInfo, SemInputs


if TYPE_CHECKING:
    from typing import Optional


class JacLLM:
    """Jac LLM."""

    @staticmethod
    def with_llm(
        file_loc: str,
        model: Any,  # noqa: ANN401
        model_params: dict[str, Any],
        scope: str,
        incl_info: list[LLMInfo],
        excl_info: list[LLMInfo],
        inputs: list[SemInputs],
        outputs: tuple,
        action: str,
    ) -> Any:  # noqa: ANN401
        """Jac's with_llm feature."""
        from jaclang.plugin.feature import pm

        return pm.hook.with_llm(
            file_loc=file_loc,
            model=model,
            model_params=model_params,
            scope=scope,
            incl_info=incl_info,
            excl_info=excl_info,
            inputs=inputs,
            outputs=outputs,
            action=action,
        )

    @staticmethod
    def get_semstr_type(
        file_loc: str, scope: str, attr: str, return_semstr: bool
    ) -> Optional[str]:
        """Jac's get_semstr_type feature."""
        from jaclang.plugin.feature import pm

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
