# setup.py
from setuptools import setup, find_packages

setup(
    name="show_plugin",
    version="0.1",
    package_data={
        "": ["*.ini"],
    },
    packages=find_packages(include=["show_plugin", "show_plugin.*"]),
    entry_points={
        "jac": ["gr = show_plugin.cmd_plugin:JacCliFeature"],
    },
)
