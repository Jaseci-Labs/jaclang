"""Jaclang setup file."""

from __future__ import annotations

from setuptools import find_packages, setup  # type: ignore


VERSION = "0.0.1"

setup(
    name="jaclang-fastapi",
    version=VERSION,
    packages=find_packages(include="jaclang_fastapi"),
    install_requires=["fastapi==0.109.0", "pydantic==2.6.0"],
    package_data={},
    entry_points={
        "jac": ["walkerapi = jaclang_fastapi.walkerapi:JacFeature"],
    },
    author="Jason Mars",
    author_email="jason@jaseci.org",
    url="https://github.com/Jaseci-Labs/jaclang",
)
