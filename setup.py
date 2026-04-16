"""
To install the library, run the following

python setup.py install

prerequisite: setuptools
http://pypi.python.org/pypi/setuptools

get the dependencies and installs

"""
from setuptools import find_packages, setup

with open("requirements.txt", encoding="utf-8") as f:
    INSTALL_REQUIRES = [x.strip() for x in f.read().split("\n")]

setup(
    name="eda-schema",
    description="Datamodel Schema for Electronic Design Automation.",
    version="1.0.0",
    py_modules=["eda_schema"],
    install_requires=INSTALL_REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    # package_data={"pynet": ["pynet/parser/verilog_technology_metadata.yaml"]},
)
