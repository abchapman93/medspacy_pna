from setuptools import setup, find_packages
from sys import platform

# read the contents of the README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="medspacy_pna",
    version="0.0.0.1",
    description="Flexible medspaCy NLP pipeline for detecting assertions of pneumonia in different clinical notes.",
    author="alec.chapman",
    author_email="alec.chapman@hsc.utah.edu",
    packages=["medspacy_pna"],
    install_requires=[
        "medspacy>=0.2.0.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)