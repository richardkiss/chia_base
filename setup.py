from setuptools import setup, find_packages  # type: ignore

packages = find_packages(where=".", include=["*"])

setup(
    packages=packages,
)
