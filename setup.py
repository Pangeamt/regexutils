# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.txt') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='regexutils',
    version='0.1.1',
    description='Utilities for applying regexes',
    long_description=readme,
    author='Pangeamt - Hans Degroote',
    author_email='h.degroote@pangeanic.com',
    license=license,
    packages=find_packages(),
    install_requires=[
        "regex",
        "importlib_resources",
        "spacy",
        "unidecode",
    ],
    package_data={'': ['files/*.txt', 'files/*.csv']},
)