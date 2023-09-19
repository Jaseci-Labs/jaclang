"""Jaclang setup file."""

from setuptools import find_packages, setup  # type: ignore

VERSION = "0.0.1"

setup(
    name="jackernel",
    version=VERSION,
    packages=find_packages(include=["jackernel", "jackernel.*"]),
    install_requires=["ipykernel==6.19.2", "pygments==2.10.0", "jaclang"],
    package_data={
        "": ["*.ini", "*.jac", "*.py"],
    },
    entry_points={
        "console_scripts": [
            "install_jackernel = jackernel.install_kernel:install_kernel",
        ],
    },
    url="https://github.com/Jaseci-Labs/jaclang/tree/main/support/kernel",
)
