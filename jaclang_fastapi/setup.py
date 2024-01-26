"""Jaclang setup file."""

from __future__ import annotations

from setuptools import find_packages, setup  # type: ignore


VERSION = "0.0.1"

setup(
    name="jaclang-fastapi",
    version=VERSION,
    packages=find_packages(),
    install_requires=[],
    package_data={
        "": [],
    },
    entry_points={},
    author="Jason Mars",
    author_email="jason@jaseci.org",
    url="https://github.com/Jaseci-Labs/jaclang",
)
