import unittest
import os
import sys
from setuptools import setup, find_packages
from distutils.core import Command

from chatbot_builder import __version__ as version

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
]

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='chatbot_builder',
    version=version,
    description=('A discord chatbot that is programmed interactively by discord users'),
    long_description=long_description,
    url='http://github.com/eriknyquist/deep_space_trader',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    install_requires=dependencies,
    packages=['chatbot_builder']
)
