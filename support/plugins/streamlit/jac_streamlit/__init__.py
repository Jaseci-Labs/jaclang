"""Streamlit of Jac."""

from jac_streamlit.app_test import JacAppTest as AppTest


def run_streamlit(basename: str, dirname: str) -> None:
    """Run the Streamlit application."""
    from jaclang import jac_import
    from jaclang.plugin.feature import JacFeature as Jac

    Jac.create_context(base_path=dirname)
    jac_import(
        basename, base_path=dirname, reload_module=True
    )  # TODO: need flag to force reload here
    Jac.close_context()


__all__ = ["AppTest", "run_streamlit"]
