# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='regexutils',
    version='0.1.0',
    description='utilities for applying regexes',
    long_description=readme,
    author='Pangeanic - Hans Degroote',
    author_email='h.degroote@pangeanic.com',
    url='',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)