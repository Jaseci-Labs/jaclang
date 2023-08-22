"""jaclang_smartimport setup file."""
from setuptools import setup

setup(
    name="jaclang_smartimport",
    version="0.0.1",
    py_modules=["smartimport"],
    entry_points={
        "jaclang.plugins": [
            "jac_red_import = jaclang_smartimport.smartimport:jac_red_import_override",
        ],
    },
)
