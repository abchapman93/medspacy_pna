from setuptools import setup, find_namespace_packages
from sys import platform

# read the contents of the README file
import os
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# function to recursively get files for resourcee
def package_files(directory):
    paths = []
    for (p, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", p, filename))
    return paths

resource_files = package_files("./medspacy_pna/resources")

setup(
    name="medspacy_pna",
    version="0.0.0.3",
    description="Flexible medspaCy NLP pipeline for detecting assertions of pneumonia in different clinical notes.",
    author="alec.chapman",
    author_email="alec.chapman@hsc.utah.edu",
    packages=find_namespace_packages(),
    install_requires=[
        "medspacy>=0.2.0.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_data={"medspacy_pna": resource_files},
)
