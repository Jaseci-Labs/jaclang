"""Setting up the 'show' cli command package."""

from setuptools import find_packages, setup

setup(
    name="show",
    version="0.1",
    package_data={
        "": ["*.ini"],
    },
    packages=find_packages(include=["show", "show.*"]),
    entry_points={
        "jac": ["show = show.show_plugin:JacCliFeature"],
    },
)
