"""Packaging glue for the EDA-Schema project."""
from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
INSTALL_REQUIRES = [
    line.strip()
    for line in README.parent.joinpath("requirements.txt").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
DEV_REQUIRES = [
    line.strip()
    for line in README.parent.joinpath("requirements-dev.txt").read_text(encoding="utf-8").splitlines()
    if line.strip()
]

setup(
    name="eda-schema",
    version="2.0.0",
    description="Multimodal property graph schema and dataset tooling for EDA.",
    long_description=README.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/drexel-ice/eda-schema",
    author="Pratik Shrestha",
    author_email="ps937@drexel.edu",
    license="Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    keywords="electronic design automation property graph dataset analysis",
    python_requires=">=3.11",
    packages=find_packages(include=["eda_schema", "eda_schema.*"]),
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        "Documentation": "https://github.com/drexel-ice/eda-schema#readme",
        "Source": "https://github.com/drexel-ice/eda-schema",
        "Issue Tracker": "https://github.com/drexel-ice/eda-schema/issues",
    },
)
