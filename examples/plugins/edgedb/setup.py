"""Jaclang setup file."""

from __future__ import annotations

from setuptools import find_packages, setup  # type: ignore


VERSION = "0.0.1"

setup(
    name="jaclang-edgedb",
    version=VERSION,
    packages=find_packages(include=["jaclang_edgedb", "jaclang_edgedb.*"]),
    install_requires=["edgedb==1.8.0"],
    package_data={
        "": ["*.ini"],
    },
    entry_points={
        "jac": ["walkerapi = jaclang_edgedb.walkerapi:JacFeature"],
    },
    author="Jason Mars",
    author_email="jason@jaseci.org",
    url="https://github.com/Jaseci-Labs/jaclang",
)
