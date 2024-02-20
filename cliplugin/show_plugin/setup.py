# setup.py
from setuptools import setup, find_packages

setup(
    name="show_plugin",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["show_plugin = show_plugin.cmd_plugin:JacCliImpl.gr"],
        "cli": ["gr = show_plugin.cmd_plugin:JacCliImpl.gr"],
    },
)
