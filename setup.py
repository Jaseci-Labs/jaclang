"""Jaclang setup file."""

from __future__ import annotations

from jaclang.compiler import generate_static_parser

from setuptools import find_packages, setup  # type: ignore


generate_static_parser(force=True)


VERSION = "0.6.0"

setup(
    name="jaclang",
    version=VERSION,
    packages=find_packages(include=["jaclang", "jaclang.*"]),
    install_requires=[],
    package_data={
        "": ["*.ini", "*.lark"],
    },
    entry_points={
        "console_scripts": [
            "jac = jaclang.cli.cli:start_cli",
        ],
    },
    extras_require={"llms": ["mtllm"]},
    author="Jason Mars",
    author_email="jason@jaseci.org",
    url="https://github.com/Jaseci-Labs/jaclang",
)
