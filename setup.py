from setuptools import find_packages, setup

setup(
    packages=find_packages(exclude=["ez_setup"]),
    include_package_data=True,
)
