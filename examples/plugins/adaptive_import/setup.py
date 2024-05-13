from setuptools import setup, find_packages

setup(
    name="jaclang-adaptive_import",
    version="1.0.0",
    packages=find_packages(),
    package_data={"adaptive_import": ["library_data_dict.json"]},
    include_package_data=True,
    install_requires=[
        "ray[client]",
        "asyncio",
    ],
    entry_points={
        "jac": ["adaptive_import = adaptive_import.adaptive_import:JacFeature"],
    },
    author="Ashish Mahendra/Ashish Agarwal",
    author_email="ashish.mahendra@jaseci.org, ashish.agarwal@jaseci.org",
    description="Adaptive import plugin for Jaclang with Ray integration",
)
