"""Jaclang setup file."""

from __future__ import annotations

from setuptools import find_packages, setup  # type: ignore


VERSION = "0.0.1"

setup(
    name="jaclang-edgedb",
    version=VERSION,
    packages=find_packages(include=["jaclang_edgedb", "jaclang_edgedb.*"]),
    install_requires=[
        "edgedb==1.8.0",
        "nest-asyncio==1.6.0",
        "fastapi==0.109.2",
        "uvicorn==0.27.0.post1",
        "gunicorn==21.2.0",
        "orjson==3.1.95",
    ],
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
